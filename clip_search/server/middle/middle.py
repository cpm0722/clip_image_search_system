import os
import time
import argparse
import logging
import requests
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from flask import Flask, g, request

import clip_search.utils
from clip_search.config import PORT_MIDDLE, ADDR_INFERENCE, PORT_INFERENCE, PATH_DIR, SEARCH_SERVER


app = Flask(__name__)


# post a json data
def post_json(post_argument):
    url = post_argument[0]
    data = post_argument[1]
    session = post_argument[2]
    idx = post_argument[3]
    try:
        return session.post(url, json=data)
    except Exception as e:
        logging.warn(f"[EXCEPTION in {idx}] {e}\n[URL] {url}")
        return e


# ShardManager for many search server
class ShardManager:
    def __init__(self, server_list, k_margin=1.2):
        self.server_list = server_list
        self.server_cnt = len(self.server_list)
        self.k_margin = k_margin  # seach extra images more considering duplicate images
        self.sessions = [requests.Session() for server in self.server_list]
        self.pool = ThreadPoolExecutor(max_workers=self.server_cnt)

    # send request concurrently to search servers
    def send_request(self, url, query, k):
        data = {'query': query, 'k': int(k*self.k_margin)}
        post_argument_list = [(f"http://{self.server_list[idx]['address']}:{self.server_list[idx]['port']}{url}", data, self.sessions[idx], idx) for idx in range(self.server_cnt)]
        responses = list(self.pool.map(post_json, post_argument_list))
        return responses

    # merge responses as one list
    # remove exception (Connection Error, Response Error...)
    def merge_response(self, responses):
        score = []
        path = []
        hash = []
        index = []
        for response in responses:
            if type(response) == requests.models.Response and response.ok:
                length = len(response.json()['score'])
                score.extend(response.json()['score'])
                path.extend(response.json()['path'])
                hash.extend(response.json()['hash'])
                index.extend([response.json()['index']]*length)
        return score, path, hash, index

    # sort responses (criterion: score)
    def sort_response(self, score, path, index):
        if len(path) == 0:
            return [], [], []
        sorted_idx = np.flip(np.argsort(score))
        sorted_score = [score[idx] for idx in sorted_idx]
        sorted_path = [path[idx] for idx in sorted_idx]
        sorted_index = [index[idx] for idx in sorted_idx]
        return sorted_score, sorted_path, sorted_index

    # total request process
    def request(self, url, query, k):
        responses = clip_search.utils.measure_elapsed_time(lambda : self.send_request(url, query, k), "send_request")
        score, path, hash, index = clip_search.utils.measure_elapsed_time(lambda : self.merge_response(responses), "merge_response")
        duplicated_removed_score, duplicated_removed_path, duplicated_removed_index = clip_search.utils.measure_elapsed_time(lambda : clip_search.utils.remove_duplicated_images(score, path, hash, index), "remove_duplicated_images")
        sorted_score, sorted_path, sorted_index = self.sort_response(duplicated_removed_score, duplicated_removed_path, duplicated_removed_index)
        sorted_url = [clip_search.utils.convert_path_to_url(path) for path in sorted_path]
        sorted_dataset = [path.split("/")[0] for path in sorted_path]
        k=min(k, len(sorted_score))
        return sorted_score[:k], sorted_url[:k], sorted_dataset[:k], sorted_index[:k]

# search for images similar to text query
@app.route("/search", methods=(["POST"]))
def search():
    # load shard manager
    shard_manager = g.get("shard_manager", None)
    if shard_manager is None:
        shard_manager = ShardManager(SEARCH_SERVER)
        g.shard_manager = shard_manager
    # request from front-end
    request_text = request.get_json()['input_text']
    k = int(request.get_json()['k'])
    mclip = request.get_json()['mclip']

    if mclip:
        MODEL_NAME = "mclip"
    else:
        MODEL_NAME = "clip"

    # inference server healthy check
    try:
        healthy = requests.get(f"http://{ADDR_INFERENCE}:{PORT_INFERENCE}/ping")
    except:
        logging.error("inference healthy check response error")
        status_code = 500
        return {}, status_code
    else:
        healthy = healthy.json()['status']
        if healthy != 'Healthy':
            logging.error("inference server is not healthy!")
            status_code = 500
            return {}, status_code

    # send request to inference server
    try:
        response = requests.post(f"http://{ADDR_INFERENCE}:{PORT_INFERENCE}/predictions/{MODEL_NAME}", json={'input_text': request_text})
    except:  # inference server error
        logging.error("inference response 500 error")
        status_code = 500
        return {}, status_code
    else:    # inference server send a response
        status_code = response.status_code
        status = status_code // 100

        # inference server response error
        if status != 2 and status != 3:
            logging.error(f"inference response error {status_code}")
            return {}, status_code

    # send request to search server with shard manager
    score, path, dataset, index = shard_manager.request('/search', response.json()['feature'], k)

    return {'score': score, 'path': path, 'dataset': dataset, 'index': index}


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wsgi", type=str, default="gunicorn", choices=["gunicorn", "waitress"],
                        help="[default: gunicorn]\n"
                             "Flask's WSGI")
    parser.add_argument("--gunicorn-num-workers", type=int, default=mp.cpu_count()*2,
                        help="[default: 28]\n"
                             "number of workers when using gunicorn as Flask's WSGI")
    parser.add_argument("--num-threads", type=int, default=8,
                        help="[default: 8]\n"
                             "number of threads(in each process) for Flask's WSGI")
    return parser


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    global parser
    parser = get_parser()
    args = parser.parse_args()

    clip_search.utils.wsgi_serve(app, args.wsgi, "0.0.0.0", PORT_MIDDLE, args.gunicorn_num_workers, args.num_threads)
