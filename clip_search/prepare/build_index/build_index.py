import os
import sys
import time
import argparse
import logging
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

import n2

import clip_search.utils
from clip_search.config import INDEX_DIR, EMBEDDING_DIR, FEATURE_DIM


# load datasets from (many) .pt files
# add features to HNSW index
# return: path list, hash list
def add_dataset_to_index(index, datasets):

    path_list = []
    hash_list = []
    for data in clip_search.utils.read_datasets(datasets):
            path_list.extend(data['path'])
            hash_list.extend(data['hash'])
            [index.add_data(feature.tolist()) for feature in data['feature']]
    return path_list, hash_list


# build HNSW index
def build_index():
    global parser
    args = parser.parse_args()

    index = n2.HnswIndex(FEATURE_DIM, metric="dot")

    add_start_time = time.time()
    path_list, hash_list = add_dataset_to_index(index, args.dataset)
    add_end_time = time.time()
    add_elapsed_time = add_end_time - add_start_time
    logging.info(f"add elapsed time: {add_elapsed_time:.2f}s")

    build_start_time = time.time()
    index.build(m = args.hnsw_m,
                max_m0 = args.hnsw_m * 2,
                ef_construction = args.ef_construction,
                mult = None,
                neighbor_selecting = "heuristic",
                graph_merging = "skip",
                n_threads = args.num_threads)
    build_end_time = time.time()
    build_elapsed_time = build_end_time - build_start_time
    logging.info(f"build elapsed time: {build_elapsed_time:.2f}s")

    total_elapsed_time = add_elapsed_time + build_elapsed_time
    logging.info(f"total elapsed time: {total_elapsed_time:.2f}s")
    return index, path_list, hash_list


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, nargs="+", required=True,
                        help="[REQUIRED]\n"
                             "list of dataset's name")
    parser.add_argument("--index", type=int, required=True,
                        help="[REQUIRED]\n"
                             "index number for saving file, the file will be saved to {INDEX_DIR}/{index}.pt")
    parser.add_argument("--hnsw-m", type=int, default=10,
                        help="[default: 10]\n"
                             "HNSW index's M value")
    parser.add_argument("--ef-construction", type=int, default=150,
                        help="[default: 150]\n"
                             "HNSW index's ef_construction value")
    parser.add_argument("--log-dir", type=str, default="logs",
                        help="[default: \"logs\"]\n"
                             "the path of log directory\n"
                             "if log_dir is not empty string, the stdout will be redirected to {log_dir}/{index}.txt"
                             "if log_dir is a empty string, stdout will be maintained")
    parser.add_argument("--num-threads", type=int, default=128,
                        help="[default: 128]\n"
                             "number of thread for building HNSW index")
    return parser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    global parser
    parser = get_parser()
    args = parser.parse_args()

    os.makedirs(args.log_dir, exist_ok=True)

    index_file_path = os.path.join(INDEX_DIR, f"{args.index:03d}.pt")
    if os.path.isfile(index_file_path):
        logging.error(f"{index_file_path} is already exists!")
        sys.exit(0)

    # stdout redirecting for logging
    if len(args.log_dir):
        sys.stdout = open(os.path.join(args.log_dir, f"{args.index:03d}.txt"), "w")

    # build index
    hnsw_index, path_list, hash_list = build_index()

    # save index, path_list, hash_list as file
    clip_search.utils.save_index(hnsw_index, args.index)
    clip_search.utils.save_path_list(path_list, args.index)
    clip_search.utils.save_hash_list(hash_list, args.index)

    sys.stdout.close()
