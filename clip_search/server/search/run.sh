#!/bin/bash

PYTHON=`which python`

PYTHONPATH=$PYTHONPATH nohup $PYTHON search.py --server-index 0 --index 0 &
