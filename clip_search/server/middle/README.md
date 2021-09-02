# Middle Server

### Summary  
middle server입니다.  
1. front server로부터 text query를 전달 받습니다.  
2. text query를 inference server에 전송해 text feature를 전달 받습니다.  
3. text feature를 다수의 search server에 동시에 전송한 뒤, 검색 결과(image path, score, hash 등)을 받습니다. (**Sharding**)  
4. 검색 결과를 hash를 기준으로 중복을 제거합니다.  
5. 검색 결과를 score 기준으로 정렬하고, 상위 k개만을 front server에 전달합니다.  

### Usage  

```
python middle.py [--wsgi] [--gunicorn-num-workers]
```

* `wsgi`  
	flask의 WSGI를 선택합니다. 
	`\"gunicorn\"`이나 `\"waitress\"`를 입력할 수 있습니다. default는 `\"gunicorn\"`입니다.  
* `gunicorn-num-workers`  
	flask의 WSGI로 `\"gunicorn\"`을 선택했을 때의 process 개수입니다.  
	정수을 입력받습니다. default는 `28`입니다.  

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

* Sequential(non-concurrency) requests Performance  
	* #req/sec: 78.32  
	* time/req: 1682.251 ms  
* Concurrent(ThreadPool) requests Performance  
	* #req/sec: 352.51  
	* time/req: 332.852 ms  
