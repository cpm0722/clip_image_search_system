import os
import time
import logging
import pickle
import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import imagehash
import n2

from clip_search.config import FEATURE_DIM, INDEX_DIR, PATH_DIR, HASH_DIR, EMBEDDING_DIR, ADDR_IMAGE, PORT_IMAGE


def measure_elapsed_time(func, func_str, ms=True):
    start_time = time.time()
    ret = func()
    end_time = time.time()
    elapsed_time = end_time - start_time
    if ms == True:
        logging.info(f"{func_str} elapsed_time: {elapsed_time*1000:.2f}ms")
    else:
        logging.info(f"{func_str} elapsed_time: {elapsed_time:.2f}s")
    return ret


# warm up for HNSW search
def warm_up_search(index, warm_up_count):
    if index is None or warm_up_count == 0:
        return

    for i in range(warm_up_count):
        query = F.normalize(torch.rand(1, FEATURE_DIM), p=2, dim=-1).squeeze(0).tolist()
        index.search_by_vector(query, 100, ef_search=300, include_distances=False)
    logging.info(f"[{os.getpid()}] warmup finish.")


# Flask app serving with wsgi
def wsgi_serve(app, wsgi, host, port, num_workers=1, num_threads=1, search_server=False, index=None, warm_up=0):
    if search_server == True:
        assert index is not None

    # using waitress
    if wsgi == "waitress":
        if search_server == True:
            warm_up_search(index, warm_up)
        import waitress
        waitress.serve(app, host=host, port=port, threads=num_threads, connection_limit=65536, asyncore_use_poll=True)

    # using gunicorn
    elif wsgi == "gunicorn":
        from gunicorn.app.base import BaseApplication
        from gunicorn.six import iteritems
        options = {
            'bind': f"{host}:{port}",
            'workers': num_workers,
            'threads': num_threads,
        }
        if search_server == True:
            options['post_fork'] = lambda server, worker: warm_up_search(index, warm_up)

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                config = dict([(key, value) for key, value in iteritems(self.options)
                               if key in self.cfg.settings and value is not None])
                for key, value in iteritems(config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        StandaloneApplication(app, options).run()
    else:
        logging.error("wsgi argument error. It should be in ['gunicorn', 'waitress'].")


# save HNSW n2 index as file
def save_index(index, index_num):
    os.makedirs(INDEX_DIR, exist_ok=True)
    index.save(os.path.join(INDEX_DIR, f"{index_num:03d}.pt"))


# load HNSW n2 index from file
def load_index(index_num, mmap=True):
    index = n2.HnswIndex(FEATURE_DIM, metric='dot')
    index.load(os.path.join(INDEX_DIR, f"{index_num:03d}.pt"), use_mmap=mmap)
    return index


# save path list as file
def save_path_list(path_list, index_num):
    os.makedirs(PATH_DIR, exist_ok=True)
    with open(os.path.join(PATH_DIR, f"{index_num:03d}.pkl"), "wb") as f:
        pickle.dump(path_list, f)


# load path list from file
def load_path_list(index_num):
    with open(os.path.join(PATH_DIR, f"{index_num:03d}.pkl"), "rb") as f:
        path_list = pickle.load(f)
    return path_list


# save hash list as file
def save_hash_list(hash_list, index_num):
    os.makedirs(HASH_DIR, exist_ok=True)
    with open(os.path.join(HASH_DIR, f"{index_num:03d}.pkl"), "wb") as f:
        pickle.dump(hash_list, f)


# load hash list from file
def load_hash_list(index_num):
    with open(os.path.join(HASH_DIR, f"{index_num:03d}.pkl"), "rb") as f:
        hash_list = pickle.load(f)
    return hash_list


# load datasets from (many) .pt files
def read_datasets(datasets):
    if type(datasets) == str:
        datasets = [datasets]

    for dataset in datasets:
        logging.info(f"**********{dataset}**********")
        dataset_path = os.path.join(EMBEDDING_DIR, dataset)
        if not os.path.isdir(dataset_path):
            logging.error(f"{dataset_path} doesn't exists!")
            continue

        for i in range(1000):  # read 'EMBEDDING_DIR/dataset/xxx.pt
            fname = f"{i:03d}.pt"
            file_path = os.path.join(dataset_path, fname)

            if os.path.isfile(file_path):
                content = torch.load(file_path, map_location="cpu")
                assert len(content['path']) == content['feature'].shape[0]
                yield content
            else:
                break


# features generator
def generate_features(datasets):
    for content in read_datasets(datasets):
        yield content['embed']


# path_list generator
def generate_path_list(datasets):
    for content in read_datasets(datasets):
        yield content['path']


# path_list generator
def generate_hash_list(datasets):
    for content in read_datasets(datasets):
        yield content['hash']


# convert a relative path to abs path
def convert_path_to_url(path):
    root_path = ""
    dataset, *keys = path.split('/')

    web_prefix = f"{ADDR_IMAGE}:{PORT_IMAGE}/dataset"
    s3_prefix = "https://s3-us-east-2.amazonaws.com"
    if dataset == "CC12M":
        dataset_path = os.path.join(web_prefix, "CC12M")
    elif dataset == "imagenet21k":
        dataset_path = os.path.join(web_prefix, "imagenet21k")
    elif dataset == "openimages":
        dataset_path = os.path.join(web_prefix, "openimages")
    elif dataset == "signals17M":
        dataset_path = os.path.join(web_prefix, "signals17M")
    elif dataset == "my-s3-bucket-name":
        dataset_path = os.path.join(s3_prefix, dataset)
    else:
        logging.error(f"path:{path} is incorrect.")
        return ""

    return path.replace(dataset, dataset_path)


# convert imagehash to integer
def convert_hash_to_integer(hash):
    integer = 0
    for bit in hash.hash.reshape(-1):
        integer = (integer << 1) + int(bit)
    return integer


# remove duplicated images (criterion: imagehash)
def remove_duplicated_images(score_list, path_list, hash_list, server_index_list):
    if len(path_list) == 0:
        return [], [], []

    hash_dict = defaultdict(list)
    for idx, hash in enumerate(hash_list):
        hash_dict[hash].append(idx)
    dup_generator = (index_list[1:] for index_list in hash_dict.values() if len(index_list)>1)

    duplicated_index = []
    [duplicated_index.extend(dup) for dup in dup_generator]

    duplicated_removed_index = np.setdiff1d(np.arange(len(path_list)), np.array(duplicated_index))
    duplicated_removed_score = [score_list[idx] for idx in duplicated_removed_index]
    duplicated_removed_path = [path_list[idx] for idx in duplicated_removed_index]
    duplicated_removed_server_index = [server_index_list[idx] for idx in duplicated_removed_index]
    return duplicated_removed_score, duplicated_removed_path, duplicated_removed_server_index
