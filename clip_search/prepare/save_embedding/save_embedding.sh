#!/bin/bash

PYTHON=`which python3`

NUM_GPU=1

DATASET=openimages
PATH_FILE=~/dataset/${DATASET}/path.txt

CLIP_MODEL_NAME=RN50x4

BATCH_SIZE=32
BATCH_PER_INFERENCE=4
INFERENCE_PER_FILE=512

NUM_WORKERS=16
NUM_THREADS=8

LOG_DIR=logs

if [[ $# -eq 0 ]]; then
    STORAGE=s3
else
    STORAGE=$1
    if [[ ${STORAGE} != "disk" && ${STORAGE} != "s3" ]]; then
        echo Usage: bash save_embedding.sh [disk || s3]
        exit
    fi
fi

### storage == s3
REGION_NAME=us-east-2
BUCKET_NAME=my-s3-bucket-name
RETRY=1
TIMEOUT=1
PROXY_HTTP=http://proxy.example.io:10000
PROXY_HTTPS=http://proxy.example.io:10000
### storage == disk
TARGET_DIR=~/dataset/${DATASET}

### get PATH_FILE's line count
LINE_CNT=`wc -l < ${PATH_FILE}`

### get number of files for embedding save
FILE_SIZE=$((${BATCH_SIZE}*${BATCH_PER_INFERENCE}*${INFERENCE_PER_FILE}))  # how many embeddings in each file
FILE_CNT=$((${LINE_CNT} / ${FILE_SIZE}))                                   # how many files for save embeddings

### get number of files per each process(GPU)
FILE_PER_PROCESS=$((${FILE_CNT} / ${NUM_GPU}))
if [[ $((${FILE_CNT} % ${NUM_GPU})) -ne 0 ]]; then
    FILE_PER_PROCESS=$((${FILE_PER_PROCESS} + 1))
fi

### get number of lines per each process(GPU)
LINE_PER_PROCESS=$((${FILE_PER_PROCESS} * ${FILE_SIZE}))

echo DATASET: ${DATASET}
echo STORAGE: ${STORAGE}
echo NUM_GPU: ${NUM_GPU}

### run processes(GPUs)
for ((i = 0; i < ${NUM_GPU}; i++)); do
    START_LINE=$((${LINE_PER_PROCESS} * ${i}))
    END_LINE=$((${START_LINE} + ${LINE_PER_PROCESS}))
    if [[ ${i} -eq $((${NUM_GPU} - 1)) ]]; then
        END_LINE=${LINE_CNT}
    fi
    echo "start: ${START_LINE}, end: ${END_LINE}"

    CUDA_VISIBLE_DEVICES=$i ${PYTHON} save_embedding.py \
    --dataset               ${DATASET} \
    --path-file             ${PATH_FILE} \
    --clip-model-name       ${CLIP_MODEL_NAME} \
    --batch-size            ${BATCH_SIZE} \
    --batch-per-inference   ${BATCH_PER_INFERENCE} \
    --inference-per-file    ${INFERENCE_PER_FILE} \
    --num-workers           ${NUM_WORKERS} \
    --num-threads           ${NUM_THREADS} \
    --start-line            ${START_LINE} \
    --end-line              ${END_LINE} \
    --process-index         ${i} \
    --log-dir               ${LOG_DIR} \
    --storage               ${STORAGE} \
    --target-dir            ${TARGET_DIR} \
    --bucket-name           ${BUCKET_NAME} \
    --region-name           ${REGION_NAME} \
    --timeout               ${TIMEOUT} \
    --retry                 ${RETRY} \
    --http-proxy            ${PROXY_HTTP} \
    --https-proxy           ${PROXY_HTTPS} \
    --no-proxy &
done
