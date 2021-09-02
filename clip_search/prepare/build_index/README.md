# Build Index

### Summary  
HNSW index를 build하고, 이를 disk에 저장하는 사전 준비 과정입니다.  
1. [Save Embedding](/clip_search/prepare/save_embedding)에서 생성한 file들을 읽어들입니다.  
2. image features를 HNSW index에 insert합니다.  
3. HNSW index를 build합니다.  
4. HNSW index와 index에 포함된 image에 해당하는 image path, hash을 disk에 각각 1개의 file로 저장합니다.  

### Usage  

```
python build_index.py [--dataset] [--index] [--hnsw-m] [--ef-construction] [--log-path] [--num-threads]
```
* `dataset`  
	불러올 dataset의 목록입니다. `{EMBEDDING_DIR}` directory를 탐색하며 인자로 받은 `{dataset}`에 해당되는 directory들을 찾아 [Save Embedding](../save_embedding) 과정에서 생성된 file들을 읽어들입니다.  
	1개 이상의 문자열을 입력받습니다. 필수 argument입니다.  
* `index`  
	저장할 data의 index 번호입니다. 
	HNSW index file은 `{INDEX_DIR}/{index}.pt`로, path file은 `{PATH_DIR}/{index}.pkl`로, hash file은 `{HASH_DIR}/{index}.pkl`에 저장됩니다.  
	정수를 입력받습니다. 필수 argument입니다.  
* `hnsw-m`  
	HNSW index build 과정에서 사용하는 `m` value입니다.  
	정수를 입력받습니다. default는 `10`입니다.  
* `ef_construction`  
	HNSW index build 과정에서 사용하는 `ef_construction` value입니다.  
	정수를 입력받습니다. default는 `150`입니다.  
* `log_dir`  
	log file을 저장하는 directory path입니다. `{log_dir}/{index}.txt`에 stdout이 redirect되게 됩니다.  
	만약 빈 문자열일 경우, stdout을 redirect하지 않습니다.  
	문자열을 입력받습니다. default는 `"logs/"`입니다.  
* `num_threads`  
	HNSW index를 build 과정에서 사용할 thread 개수입니다.  
	정수를 입력받습니다. default는 `28`입니다.  
	
### Parameter Search  
* total size: 1M  
* sample size: 1K  
* `ef_construction`: 150  
* Hardware  
	* CPU: Intel Xeon 2.20GHz x 56  
	* RAM: 488GB  

| `m` | `ef_search` | latency(mean) | 100@recall |
| ---:| ----:| -----:| ------:|
|  5  |  200 | 5.804 | 87.40% |
|  5  |  300 | 2.573 | 91.30% |
|  5  |  400 | 2.785 | 93.20% |
|  5  |  500 | 2.916 | 94.32% |
|  5  | 1000 | 4.030 | 96.72% |
| 10  |  200 | 6.191 | 95.79% |
| **10**  |  **300** | **3.057** | **97.44%** |
| 10  |  400 | 3.374 | 98.11% |
| 10  |  500 | 3.707 | 98.45% |
| 10  | 1000 | 5.093 | 99.01% |
| 20  |  200 | 6.614 | 98.21% |
| 20  |  300 | 3.619 | 98.84% |
| 20  |  400 | 4.096 | 99.06% |
| 20  |  500 | 4.586 | 99.15% |
| 20  | 1000 | 6.857 | 99.28% |
| 40  |  200 | 6.953 | 98.84% |
| 40  |  300 | 3.901 | 99.11% |
| 40  |  400 | 4.531 | 99.21% |
| 40  |  500 | 5.051 | 99.25% |
| 40  | 1000 | 7.549 | 99.30% |

* [HNSW paper](https://arxiv.org/abs/1603.09320)에서 제시한 default value인 `ef_construction=150`으로 fix했을 때, `m=10`, `ef_search=300`인 경우에 가장 reasonable한 latency 및 recall을 보였으므로 이를 채택했다.
