# Search Server

### Summary  
search server입니다.  
1. [Build Index](/clip_search/prepare/build_index) 단계에서 생성한 index, path, hash file들을 load합니다.  
2. middle server에서 text feature를 전송받습니다.  
3. HNSW(Hierarchical Navigable Small World) Graph를 사용한 approximated nearest neighbor vector search를 수행합니다.  
4. text feature와 가장 유사한 k개의 image features를 찾아 해당하는 image path, hash를 middle server에 전달합니다.  

### Usage  

```
python search.py [--index] [--server-index] [--wsgi] [--gunicorn-num-workers] [--warm-up-count] [--(no-)mmap]
```
* `index`  
	저장된 data의 index 번호입니다. 
	HNSW index file은 `INDEX_DIR/{index}.pt`로, path file은 `PATH_DIR/{index}.pkl`로, hash file은 `HASH_DIR/{index}.pkl`에 저장되어 있어야 합니다.  
	정수를 입력받습니다. 필수 argument입니다.  
* `server-index`  
	search server의 index 번호입니다. config에서의 search server list에서의 index 번호입니다.  
	정수를 입력받습니다. default는 `0`입니다.  
* `wsgi`  
	flask의 WSGI를 선택합니다. 
	`\"gunicorn\"`이나 `\"waitress\"`를 입력할 수 있습니다. default는 `\"gunicorn\"`입니다.  
* `gunicorn-num-workers`  
	flask의 WSGI로 `\"gunicorn\"`을 선택했을 때의 process 개수입니다.  
	정수을 입력받습니다. default는 `28`입니다.  
* `warm-up-count`  
	HNSW index를 loading한 직후, warm-up을 위한 search를 수행하는 횟수입니다.  
	정수를 입력받습니다. default는 `500`입니다.  
* `[no-]mmap`  
	HNSW index를 loading할 때, mmap을 사용하는지에 대한 flag입니다. 이 때, mmap은 기본적으로 non-lazy loading입니다.  
	`wsgi==\"gunicorn\"`으로 multiprocessing serving을 할 때에 유용합니다.  
	default는 true입니다.  


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

### Performance  

* Hardware  
	* CPU: Intel Xeon 2.20GHz x 14  
	* RAM: 122GB  
* WSGI  
	* library: gunicorn  
	* #workers: 8  
	* #threads: 8  
* Benchmark
	* Hardware  
		* CPU: Intel Xeon 2.20GHz x 56  
		* RAM: 488GB  
	* Tool: [Apache Benchmark](https://httpd.apache.org/docs/2.4/programs/ab.html)  
	* #connections: 128  
	* #requests: 10000  

* Search Performance (worst & best in 21 search servers)  
	* #req/sec  
		* worst: 1028.42  
		* best: 2176.84
	* time/req:  
		* worst: 124.463 ms  
		* best: 58.801 ms
