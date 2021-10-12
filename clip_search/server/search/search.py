import os
import time
import argparse
import logging

from flask import Flask, request
import n2

import clip_search.utils
from clip_search.config import FEATURE_DIM, EF_SEARCH, INDEX_DIR, SEARCH_SERVER, PORT_SEARCH


app = Flask(__name__)


# search for vectors similar to query(vector or id) in HNSW index
def search_HNSW(query, k):
    search_start_time = time.time()
    results = index.search_by_vector(query, k, ef_search=EF_SEARCH, include_distances=True)
    search_end_time = time.time()
    search_elapsed_time = search_end_time - search_start_time
    logging.info(f"[{os.getpid()}] search elapsed time: {search_elapsed_time*1000:.2f}ms")

    indices = [result[0] for result in results]
    scores = [result[1] for result in results]
    return indices, scores


# search for vectors similar to query(vector or id)
@app.route("/searches/text-to-images", methods=(["POST"]))
def search_text2img():
    # request from middle
    query = request.get_json()['query']
    k = request.get_json()['k']

    idx, score = search_HNSW(query, k)
    path = [path_list[i] for i in idx]
    hash = [hash_list[i] for i in idx]

    status_code = 200
    return {'score': score, 'path': path, 'hash': hash, 'index': app.config['index']}, status_code


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, required=True,
                        help="[REQUIRED]\n"
                             "index number for loading\n"
                             "index file is {INDEX_DIR}/index.pt\n"
                             "path file is {PATH_DIR}/index.pkl\n"
                             "hash file is {HASH_DIR}/hash.pkl\n")
    parser.add_argument("--server-index", type=int, default=0,
                        help="[default: 0]\n"
                             "search server index in config")
    parser.add_argument("--wsgi", type=str, default="gunicorn", choices=["gunicorn", "waitress"],
                        help="[default: \"gunicorn\"]\n"
                             "Flask's WSGI")
    parser.add_argument("--gunicorn-num-workers", type=int, default=8,
                        help="[default:28]\n"
                             "number of workers when using gunicorn as Flask's WSGI")
    parser.add_argument("--warm-up-count", type=int, default=500,
                        help="[default: 500]\n"
                             "warm-up search count")
    parser.add_argument("--mmap", dest="mmap", action="store_true",
                        help="use (non-lazy) mmap for loading HNSW index")
    parser.add_argument("--no-mmap", dest="mmap", action="store_false",
                        help="do no use mmap for loading HNSW index")
    parser.set_defaults(mmap=True)
    return parser


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    global parser
    parser = get_parser()
    args = parser.parse_args()

    global path_list
    path_list = clip_search.utils.load_path_list(args.index)
    logging.info("path_list is loaded.")

    global hash_list
    hash_list = clip_search.utils.load_hash_list(args.index)
    logging.info("hash_list is loaded.")

    global index
    index = clip_search.utils.load_index(args.index, args.mmap)
    logging.info("index is loaded.")

    app.config['index'] = args.server_index
    clip_search.utils.wsgi_serve(app=app,
                               wsgi=args.wsgi,
                               host="0.0.0.0",
                               port=PORT_SEARCH,
                               num_workers=args.gunicorn_num_workers,
                               search_server=True,
                               index=index,
                               warm_up=args.warm_up_count)
