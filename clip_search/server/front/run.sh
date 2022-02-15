#!/bin/bash

PYTHON=`which python`

nohup sudo PYTHONPATH=$PYTHONPATH $PYTHON front.py &

# sudo PYTHONPATH=$PYTHONPATH $PYTHON front.py --gunicorn-num-workers 1
