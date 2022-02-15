import os
import argparse
import logging
import requests
import multiprocessing as mp

from flask import Flask, render_template, request, make_response

import clip_search.utils
from clip_search.config import PORT_FRONT, ADDR_MIDDLE, PORT_MIDDLE

app = Flask(__name__)


@app.route("/", methods=(["GET"]))
def index():
    return render_template("index.html")


# search for images similar to text queries
@app.route("/searches/text-to-images", methods=(["POST"]))
def search_text2img():
    # request from front-end
    print(request.get_json())
    request_text = request.get_json()['input_text']
    k = request.get_json()['k']
    mclip = request.get_json()['mclip']

    try:
        logging.info(f"input_text: {request_text}, k: {k}, mclip: {mclip}")
        response = requests.post(f"http://{ADDR_MIDDLE}:{PORT_MIDDLE}/searches/text-to-images", json={'input_text': request_text, 'k': k, 'mclip': mclip})
    except:  # middle server error
        logging.error("middle response 500 error")
        status_code = 500
        return {}, status_code
    else:    # inference server send a response
        status_code = response.status_code
        status = status_code // 100

        # inference server response error
        if status != 2 and status != 3:
            logging.error(f"middle response error {status_code}")
            return {}, status_code

    return response.json(), status_code


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

    clip_search.utils.wsgi_serve(app, args.wsgi, "0.0.0.0", PORT_FRONT, args.gunicorn_num_workers, args.num_threads)
