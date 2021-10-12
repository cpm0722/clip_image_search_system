import os
import pathlib
import json

PWD = str(pathlib.Path(__file__).parent)
with open(os.path.join(PWD, "config.json"), "r") as config_file:
    config = json.load(config_file)

# front
ADDR_FRONT = config['front']['address']
PORT_FRONT = config['front']['port']

# middle
ADDR_MIDDLE = config['middle']['address']
PORT_MIDDLE = config['middle']['port']

# inference
ADDR_INFERENCE = config['inference']['address']
PORT_INFERENCE = config['inference']['port']
CLIP_MODEL = config['inference']['model-url']['clip']
MCLIP_MODEL = config['inference']['model-url']['mclip']

# search
SEARCH_SERVER = config['search']['server-list']
PORT_SEARCH = config['search']['inner-port']
EF_SEARCH = config['search']['ef-search']

# image
ADDR_IMAGE = config['image']['address']
PORT_IMAGE = config['image']['port']

# prepare
INDEX_DIR = config['prepare']['dir-path']['index-dir']
PATH_DIR = config['prepare']['dir-path']['path-dir']
HASH_DIR = config['prepare']['dir-path']['hash-dir']
EMBEDDING_DIR = config['prepare']['dir-path']['embedding-dir']
FEATURE_DIM = config['prepare']['feature-dim']
