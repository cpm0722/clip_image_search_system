# Server

### Summary

전체 server module은 [Front](/clip_search/server/front/), [Middle](/clip_search/server/middle/), [Inference](/clip_search/server/inference/), [Search](/clip_search/server/search/) 총 4개로 구성됩니다.  
이 중 inference server는 torchserver를, 그 외 3개의 module은 모두 flask + WSGI(gunicorn, waitress)를 사용합니다.  
serch server는 다수의 instance를 가질 수 있습니다.

### Config

config.json에는 실행에 필요한 server의 ipv4 address 및 port number 및 그 외 기타 정보들이 작성되어 있어야 합니다.  
* `Front`  
	* `address [str]` : front server의 ipv4 adress  
	* `port [int]` : front server의 port number  
* `Middle`  
	* `address [str]` : middle server의 ipv4 adress  
	* `port [int]` : middle server의 port number  
* `Inference`  
	* `address [str]` : inference server의 ipv4 adress  
	* `port [int]` : inference server의 port number  
	* `clip [str]` : inference server에서의 clip의 model name  
	* `mclip [str]` : inference server에서의 mclip의 model name  
* `Search`  
	* `server-list [list]` : search server의 목록, ipv4 address와 외부 port number  
	* `inner-port [int]` : search server의 내부 port number  
	* `ef-search [int]` : search server에서의 HNSW ef-search value
* `Prepare`  
	* `embedding-dir[str]` : [Save Embedding](/clip_search/prepare/save_embedding) 과정에서 embedding file을 저장하는 directory 경로, [Build Index](/clip_search/prepare/build_index) 과정에서 load
	* `index-dir [str]` : [Build Index](/clip_search/prepare/build_index) 과정에서 HNSW index file을 저장하는 directory 경로, search server에서 load
	* `path-dir [str]` : [Build Index](/clip_search/prepare/build_index) 과정에서 path file을 저장하는 directory 경로, search server에서 load
	* `hash-dir [str]` : [Build Index](/clip_search/prepare/build_index) 과정에서 hash file을 저장하는 directory 경로, search server에서 load
	* `feature-dim [int]` : CLIP embedding에서 image feature의 dimension

### Simple Usage

* [Front](/clip_search/server/front/)
	```
	python front/front.py
	```

* [Middle](/clip_search/server/middle/)
	```
	python middle/middle.py
	```

* [Inference](/clip_search/server/inference/)
	```
	torchserve --start --model-store inference/models --ts-config inference/snapshot_8.cfg
	```

* [Search](/clip_search/server/search/)
	```
	python search/search.py --server-index 0 --index 0
	```

### Performance  

* Hardware  
	* CPU: Intel Xeon 2.20GHz x 56  
	* RAM: 488GB  
* WSGI  
	* library: gunicorn  
	* #workers: 128  
	* #threads: 8  
* Benchmark
	* Hardware  
		* CPU: Intel Xeon 2.20GHz x 56  
		* RAM: 488GB  
	* Tool: [Apache Benchmark](https://httpd.apache.org/docs/2.4/programs/ab.html)  
	* #connections: 128  
	* #requests: 10000  
* #servers: 21

* Total Performance (without front server)
	* #req/sec: 330.78  
	* time/req: 318.72 ms  
