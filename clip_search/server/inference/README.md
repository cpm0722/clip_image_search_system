# Inference Server

### Summary  
inference server입니다.  
torchserve를 사용해 [CLIP](https://github.com/openai/CLIP) (+ [multilingual-CLIP](https://github.com/FreddeFrallan/Multilingual-CLIP))을 serving합니다.  

### Usage  
1. CLIP model을 torchscript의 jit.trace mode로 저장합니다.  
	```
	import torch
	torch.jit.save(model, "traced_model.pt")
	```
2. CLIP model을 archive합니다.  
	```
	torch-model-archiver --model-name CLIP --version 1.0 --serialized-file traced_model.pt --handler clip_handler.py
	```
4. config.properties를 작성합니다.  
	```
	inference_address=http://0.0.0.0:8081
	management_address=http://0.0.0.0:8082
	metrics_address=http://0.0.0.0:8083
	default_response_timeout=300
	unregister_model_timeout=300
	```
3. torchserve를 시작합니다.  
	```
	mkdir -p models && mv traced_model.pt models
	torchserve --model-store models --ts-config config.properties
	```
4. model을 등록합니다.  
	```
	curl -X POST "http://localhost:8082/models?url=/model_store/CLIP.mar&model_name=clip&initial_workers=8&batch_size=32&max_batch_delay=100"
	```
5. `logs/config`에 저장된 `snapshot.cfg`를 보관합니다.  
	이후 torchserve 실행 시에는 config.properties 대신 해당 snapshot.cfg를 불러옴으로써 위의 과정을 생략할 수 있습니다.  

* Simple Usage in 8 GPU Machine  
	```
	torchserve --start --model-store models --ts-config snapshot_8.cfg
	```
* Simple Usage in 8 GPU Machine  
	```
	torchserve --start --model-store models --ts-config snapshot_4.cfg
	```

### eager mode vs trace mode  
* Hardware  
	* CPU: Intel Xeon 2.20GHz x 28  
	* GPU: NVIDIA V100 x 2
	* RAM: 244GB  
* serving  
	* library: torchserve  
	* #workers: 2  
	* batch_size: 32  
	* max_batch_delay: 100ms  
* Benchmark
	* Hardware  
		* CPU: Intel Xeon 2.20GHz x 56  
		* RAM: 488GB  
	* Tool: [Apache Benchmark](https://httpd.apache.org/docs/2.4/programs/ab.html)  
	* #connections: 64  
	* #requests: 1000  
* eager mode Performance  
	* #req/sec: 1387.64  
	* time/req: 46.122 ms  
* **trace mode** Performance  
	* #req/sec: **1603.60**  
	* time/req: **39.910** ms  
* **trace mode**가 eager mode 대비 약 **1.2배** 좋은 성능을 보였기에, trace mode를 채택했다.  

### Performance  

* Hardware  
	* CPU: Intel Xeon 2.20GHz x 56  
	* GPU: NVIDIA V100 x 4
	* RAM: 488GB  
* serving  
	* library: torchserve  
	* #workers: 4  
	* batch_size: 32  
	* max_batch_delay: 100ms  
* Benchmark
	* Hardware  
		* CPU: Intel Xeon 2.20GHz x 56  
		* RAM: 488GB  
	* Tool: [Apache Benchmark](https://httpd.apache.org/docs/2.4/programs/ab.html)  
	* #connections: 128  
	* #requests: 10000  
* CLIP Image Encoder Backbone Model: RN50x4  

* Inference Performance  
	* #req/sec: 1924.21  
	* time/req: 66.521 ms  
