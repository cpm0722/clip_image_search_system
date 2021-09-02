#!/bin/bash

APACHE_BENCHMARK=ab

NUM_CONNECTIONS=128
NUM_REQUESTS=10000

if [[ $1 == "inference" ]]; then
	INFERENCE_SERVER=$(python3 -c 'from clip_search import config; print(f"{config.ADDR_INFERENCE}:{config.PORT_INFERENCE}")')
	$APACHE_BENCHMARK -p samples/inference.json -T application/json  -k -c $NUM_CONNECTIONS -n $NUM_REQUESTS $INFERENCE_SERVER/predictions/clip
elif [[ $1 == "search" ]]; then
	SEARCH_SERVER=$(python3 -c 'from clip_search import config; addr=config.SEARCH_SERVER[0]["address"]; port=config.SEARCH_SERVER[0]["port"]; print(f"{addr}:{port}")')
	$APACHE_BENCHMARK -p samples/search.json -T application/json  -c $NUM_CONNECTIONS -n $NUM_REQUESTS $SEARCH_SERVER/search
elif [[ $1 == "middle" ]]; then
	MIDDLE_SERVER=$(python3 -c 'from clip_search import config; print(f"{config.ADDR_MIDDLE}:{config.PORT_MIDDLE}")')
	$APACHE_BENCHMARK -p samples/middle.json -T application/json  -c $NUM_CONNECTIONS -n $NUM_REQUESTS $MIDDLE_SERVER/search
else
	echo "Usage:bash benchmark.sh [inference|search|middle]"
fi
