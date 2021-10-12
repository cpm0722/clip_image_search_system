import os
import sys
import time
import argparse
import logging
import itertools
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize
from PIL import Image
import imagehash
import boto3
import botocore

import clip
import clip_search.utils
from clip_search.config import EMBEDDING_DIR


# DataLoader's worker initialized function
# make a connection with aws s3 bucket
# load clip preprocessor
def worker_init_fn(worker_id):
    # clip preprocessor
    global transform
    transform = Compose([
        Resize(288, interpolation=Image.BICUBIC),
        CenterCrop(288),
        lambda image: image.convert("RGB"),
        ToTensor(),
        Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
    ])

    parser = get_parser()
    args = parser.parse_args()

    global storage
    storage = args.storage
    global num_threads
    num_threads = args.num_threads

    if storage == "s3":
        global bucket
        if args.proxy == True:
            proxy_definitions = {
                'http': args.http_proxy,
                'https':args.https_proxy
            }
        else:
            proxy_definitions = None
        config = botocore.config.Config(signature_version=botocore.UNSIGNED,
                                        connect_timeout=args.timeout,
                                        read_timeout=args.timeout,
                                        proxies=proxy_definitions)
        s3 = boto3.resource("s3", region_name=args.region_name, config=config)
        bucket = s3.Bucket(args.bucket_name)
        global retry
        retry = args.retry
    elif storage == "disk":
        global target_dir
        target_dir = args.target_dir


# download images from AWS s3
def request_to_s3(path):
    global bucket
    global retry
    for _ in range(retry):
        try:
            response = bucket.Object(path).get()
            body = response['Body']
        except:
            pass
        else:
            return body
    return None


# this method is recommended to call in ThreadPool
# load images
# image open with PIL
# preprocess with clip transform
# calculate hash with imagehash and casting to integer
# the type of image is torch.Tensor
# if some exception occured, it will return None instead of image
def load_images(path_list):
    global transform
    global storage

    image_list = []
    hash_list = []
    for path in path_list:
        if storage == "s3":      # load image from s3
            source = request_to_s3(path)
            if source is None:
                hash_list.append(None)
                image_list.append(None)
                continue
        elif storage == "disk":  # load image from disk
            global target_dir
            source = os.path.join(target_dir, path)

        try:
            image = Image.open(source)
            image_hash = imagehash.average_hash(image)
            image = transform(image)
        except:
            hash_list.append(None)
            image_list.append(None)
        else:
            hash_list.append(clip_search.utils.convert_hash_to_integer(image_hash))
            image_list.append(image)

    return {'image': image_list, 'hash': hash_list}


# send request concurrently with ThreadPool
def send_requests(path_list):
    global bucket
    global transform
    global num_threads
    global retry
    path_per_thread = len(path_list) // num_threads  # num_path for each thread
    splitted_path_list = [path_list[path_per_thread*idx : path_per_thread*(idx+1)] for idx in range(num_threads)]  # distribute path list to each threads
    with ThreadPoolExecutor(max_workers=len(path_list)) as pool:  # multi-threading request
        results = list(pool.map(load_images, splitted_path_list))
    image_list = []
    hash_list = []
    for result in results:
        image_list.extend(result['image'])
        hash_list.extend(result['hash'])
    return image_list, hash_list


# DataLoader's collate function
# DataLoader's each workers call this function with argument as some path_list(batch_size)
# filtering error and return {path, image, hash, error_path} as dict
def corrupt_filtering_collate(path):
    images, hashes = send_requests(path)

    assert len(path) == len(images)
    assert len(path) == len(hashes)
    if len(path) == 0:
        logging.warn("batch is empty.")

    batch_path = []
    batch_image = []
    batch_hash = []
    error_path = []
    for idx in range(len(path)):
        if images[idx] is None:          # filtering exception occured image
            error_path.append(path[idx])
        else:
            batch_path.append(path[idx])
            batch_image.append(images[idx])
            batch_hash.append(hashes[idx])

    assert len(batch_path) == len(batch_image)
    assert len(batch_path) == len(batch_hash)
    return {'path': batch_path, 'image': batch_image, 'hash': batch_hash, 'error_path': error_path}


# get clip embedding
def save_embedding(path_list):
    args = parser.parse_args()
    error_cnt_per_file = 0      # accumulated error count per file
    error_cnt = 0               # accumulated total error count
    inference_elapsed_time = 0  # accumulated inference elapsed time

    # load clip model
    device = torch.device("cuda")
    model, _ = clip.load(args.clip_model_name, jit=True)
    model = model.eval().to(device, non_blocking=True)

    error_path_list = []        # total error path list,    it will saved as file at the last
    paths_for_save = []         # path list for file save,  it will initialized as empty list at each file saving
    hashes_for_save = []        # hash list for file save,  it will initialized as empty list at each file saving
    features_for_save = []      # features for file save,    it will initialized as empty list at each file saving
    images_for_inference = []   # image(tensor) list for inference, it will initialized as empty list at each inference
    file_idx = args.start_line // (args.batch_size*args.batch_per_inference*args.inference_per_file)  # file index for saving file name

    # iterate dataloader
    dataloader = DataLoader(path_list, batch_size=args.batch_size, shuffle=False, drop_last=True, collate_fn=corrupt_filtering_collate, num_workers=args.num_workers, worker_init_fn=worker_init_fn, pin_memory=True)
    batch_idx = 0
    for batch in dataloader:
        batch_idx += 1
        assert len(batch['path']) == len(batch['image'])
        assert len(batch['path']) == len(batch['hash'])
        assert len(batch['path']) + len(batch['error_path']) == args.batch_size

        error_cnt_per_file += len(batch['error_path'])
        error_path_list.extend(batch['error_path'])
        # accumulate for saving as file
        paths_for_save.extend([os.path.join(args.dataset, path) for path in batch['path']]) # convert path to url
        hashes_for_save.extend(batch['hash'])
        images_for_inference.extend(batch['image'])

        # inference
        if batch_idx % args.batch_per_inference == 0 and len(images_for_inference) > 0:
            inference_start_time = time.time()
            batch_image = torch.stack(images_for_inference, dim=0).to(device, non_blocking=True) # convert tensor list to one tensor
            images_for_inference = [] # initialize for next inference
            # clip model inference
            features = model.encode_image(batch_image).detach()
            features = F.normalize(features, p=2, dim=1)
            features = features.cpu()
            features_for_save.append(features)
            inference_elapsed_time += time.time() - inference_start_time  # accumulate inference elapsed time

        # save as file
        if (batch_idx) % (args.batch_per_inference * args.inference_per_file) == 0 and len(features_for_save) > 0:
            features_for_save = torch.cat(features_for_save, dim=0)  # convert tensor list to one tensor
            save_file_path = os.path.join(EMBEDDING_DIR, args.dataset, f"{file_idx:03d}.pt")
            torch.save({'path': paths_for_save, 'feature': features_for_save, 'hash': hashes_for_save}, save_file_path)
            error_rate_per_file = error_cnt_per_file / (args.batch_size * args.batch_per_inference * args.inference_per_file) * 100
            error_cnt += error_cnt_per_file
            error_cnt_per_file = 0
            logging.info(f"{file_idx} file is saved, total: {features_for_save.shape[0]}, error_rate: {error_rate_per_file}")
            # initialize for next file
            paths_for_save = []
            hashes_for_save = []
            features_for_save = []
            file_idx += 1

    # save error path list
    with open(os.path.join(EMBEDDING_DIR, args.dataset, f"error_path_{args.process_index}.txt"), "w") as f:
        for path in error_path_list:
            f.write(path + '\n')

    logging.info(f"inference elapsed_time: {inference_elapsed_time:.3f}s")
    logging.info(f"total error rate: {error_cnt / (args.end_line-args.start_line) * 100:.2f}%")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True,
                        help="[REQUIRED]\n"
                             "dataset name for saving")
    parser.add_argument("--path-file", type=str, required=True,
                        help="[REQUIRED]\n"
                             "path to the text file where the paths of the images are stored")
    parser.add_argument("--clip-model-name", type=str, default="RN50x4", choices=["RN50", "RN101", "RN50x4", "RN50x16", "ViT-B/32", "ViT-B/16"],
                        help="[default: \"RN50x4\"]\n"
                             "CLIP model name")
    parser.add_argument("--batch-size", type=int, default=64,
                        help="[default: 64]\n"
                             "number of images each worker needs to process at once")
    parser.add_argument("--batch-per-inference", type=int, default=4,
                        help="[default: 4]\n"
                             "number of batch for each inference")
    parser.add_argument("--inference-per-file", type=int, default=512,
                        help="[default: 4]\n"
                             "number of batch for each inference")
    parser.add_argument("--num-workers", type=int, default=mp.cpu_count()//8,
                        help="[default: cpu_count/8]\n"
                             "number of processes for DataLoader (multiprocessing)")
    parser.add_argument("--num-threads", type=int, default=8,
                        help="[default: 8]\n"
                             "number of threads for each worker (multithreading)")
    parser.add_argument("--start-line", type=int, default=0,
                        help="[default: 0]\n"
                             "line number starting reading from path_file")
    parser.add_argument("--end-line", type=int, default=4096,
                        help="[default: 0]\n"
                             "line number ending reading from path_file")
    parser.add_argument("--process-index", type=int, default=0,
                        help="[default: 0]\n"
                             "process index number for logging")
    parser.add_argument("--log-dir", type=str, default="",
                        help="[default: \"\"]\n"
                             "the path of log directory\n"
                             "if log_dir is not empty string, the stdout will be redirected to {log_dir}/{dataset}_{process_index}.txt"
                             "if log_dir is a empty string, stdout will be maintained")
    parser.add_argument("--storage", type=str, choices=["s3", "disk"] ,default="s3",
                        help="image storage, s3 is download image from AWS s3, disk is read image file from disk")
    parser.add_argument("--target-dir", type=str, default="",
                        help="[USE ONLY storage == \"disk\"]\n"
                             "[default: \"\"]\n"
                             "root path where the image files are stored")
    parser.add_argument("--bucket-name", type=str, default="my-s3-bucket-name",
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: \"my-s3-bucket-name\"]\n"
                             "AWS S3 bucket name")
    parser.add_argument("--region-name", type=str, default="us-east-2",
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: \"us-east-2\"]\n"
                             "AWS S3 region name")
    parser.add_argument("--timeout", type=int, default=1,
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: 1]\n"
                             "timeout for request image file")
    parser.add_argument("--retry", type=int, default=5,
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: 5]\n"
                             "retry count for request image file")
    parser.add_argument("--proxy", dest="proxy", action="store_true",
                        help="use proxy for AWS S3 access")
    parser.add_argument("--no-proxy", dest="proxy", action="store_false",
                        help="do not use proxy for AWS S3 access")
    parser.add_argument("--http-proxy", type=str, default="http://proxy.example.io:10000",
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: \"http://proxy.example.io:10000\"]\n"
                             "http proxy address for AWS S3")
    parser.add_argument("--https-proxy", type=str, default="http://proxy.example.io:10000",
                        help="[USE ONLY storage == \"s3\"]\n"
                             "[default: \"http://proxy.example.io:10000\"]\n"
                             "http proxy address for AWS S3")
    parser.set_defaults(proxy=False)
    return parser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    global parser
    parser = get_parser()
    args = parser.parse_args()

    # stdout redirecting for logging
    if len(args.log_dir):
        sys.stdout = open(os.path.join(args.log_dir, f"{args.dataset}_{args.process_index}.txt"), "w")

    logging.info(f"parent PID: {os.getpid()}")
    logging.info(f"size: {args.end_line-args.start_line}")
    logging.info(f"batch_size: {args.batch_size}")
    logging.info(f"batch_per_inference: {args.batch_per_inference}")
    logging.info(f"num_workers: {args.num_workers}")

    Image.MAX_IMAGE_PIXELS = None  # Read Big Size Images
    Image.warnings.filterwarnings("ignore", "(Possibly )?corrupt EXIF data", UserWarning) # Ignore EXIF warning

    os.makedirs(args.log_dir, exist_ok=True)
    os.makedirs(os.path.join(EMBEDDING_DIR, args.dataset), exist_ok=True)

    if not os.path.isfile(args.path_file):
        logging.error(f"path file {args.path_file} doesn't exists!")
        exit(1)

    # get path list
    path_list = []
    with open(args.path_file, "r") as f:
        for line_idx, line in enumerate(itertools.islice(f, args.start_line, args.end_line)):
            path = line.strip()  # remove '\n'
            # _, *keys = path.split('/')
            # key = '/'.join(keys)
            # path_list.append(key)
            path_list.append(path)

    total_start_time = time.time()
    save_embedding(path_list)
    total_end_time = time.time()
    logging.info(f"total elapsed time: {total_end_time-total_start_time:.2f}s")

    sys.stdout.close()
