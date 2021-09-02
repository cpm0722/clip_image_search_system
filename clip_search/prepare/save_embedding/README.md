# Save Embedding

### Summary  
image dataset을 읽어들여 CLIP embedding을 추출하고, 이를 disk에 저장하는 사전 준비 과정입니다.  
GPU가 있는 instance에서만 실행 가능합니다. multi-GPU instance인 경우, 각 GPU 당 1개의 main process가 실행됩니다.  
1. image의 path가 저장된 file을 읽어들입니다.  
2. batch 단위로 disk 또는 AWS S3에서 image를 load합니다.  
3. batch 단위로 image 전처리 및 imagehash 계산을 수행합니다.  
4. image batch가 `batch_per_inference`만큼 모이면 CLIP model의 image encoder에 inference를 수행해 embedding을 추출하고, L2 Normalize합니다.  
5. inference가 `inference_per_file`만큼 수행되고 나면 embedding, path, imagehash를 disk(`EMBEDDING_DIR`)에 저장합니다.  

### Usage  

1. `save_embedding.sh` file에서 `DATASET, PATH_FILE, TARGET_DIR` 등의 값을 수정합니다.  
2. script를 실행합니다.  
	```
	bash save_embedding.sh [disk|s3]
	```

### Detail  

* `dataset`  
	불러올 dataset의 명칭입니다.  
	embedding file은 `{EMBEDDING_DIR}/{datset}`에 저장되게 됩니다.  
	문자열을 입력받습니다. 필수 argument입니다.  
* `path_file`  
	image file들의 path가 저장된 file의 경로입니다.  
	path file은 각 image path마다 `'\n'`으로 구분되며, `{dataset}/real_path` 형태로 저장되어 있습니다.  
	실제 image path는 `{dataset}`이 포함되지 않습니다.  
  `storage=="disk"`인 경우에는 `{target_dir}/real_path`가 disk에서의 실제 image path가 되고, `storage=="s3"`인 경우에는 `real_path`가 해당 bucket 내에서의 실제 image path가 됩니다.  
	embedding file로 저장될 때에 path는 `{path_file}`에 있던 `{dataset}/real_path` 형태로 저장됩니다.  
	문자열을 입력받습니다. 필수 argument입니다.  
* `clip_model_name`  
	[OpenAI/CLIP](https://github.com/openai/CLIP)에서 지원하는 CLIP image encoder의 backbone model명입니다.  
	`RN50`, `RN101`, `RN50x4`, `RN50x16`, `ViT-B/32`, `ViT-B/16` 중 하나를 입력할 수 있습니다. default는 `RN50x4`입니다.  
* `batch_size`  
	각 worker마다 처리하는 batch의 size입니다.  
	정수를 입력받습니다. default는 `64`입니다.  
* `batch_per_inference`    
	한 번의 inference를 수행할 때에 필요한 batch의 개수입니다. 즉, `{batch_per_inference}`만큼 batch를 모은 뒤 한번에 inference합니다.  
	정수를 입력받습니다. default는 `4`입니다.  
* `inference_per_file`  
	한 번의 file 저장을 수행할 때에 필요한 inference의 횟수입니다. 즉, `{inference_per_file}`만큼 inference를 수행한 뒤 그 결과를 하나의 file로 저장합니다.  
	정수를 입력받습니다. default는 `4`입니다.  
* `num_workers`  
	DataLoader에서 사용하는 worker 수입니다.  
	정수를 입력받습니다. default는 `cpu_count/8`입니다.  
* `num_threads`  
	DataLoader의 각 worker마다 부여되는 thread 수입니다.  
	정수를 입력받습니다. default는 `8`입니다.  
* `start_line`  
	`{path_file}`에서 읽어들이기 시작하는 line number입니다.  
	정수를 입력받습니다. default는 `0`입니다.  
* `end_line`  
	`{path_file}`에서 읽어들이는 마지막 line number입니다.  
	정수를 입력받습니다. default는 `4096`입니다.  
* `process_index`  
	logging에 사용할 process의 index입니다. 대개 GPU index와 동일한 값을 사용합니다.  
	정수를 입력받습니다. default는 `0`입니다.  
* `log_dir`  
	log file을 저장하는 directory path입니다. `{log_dir}/{dataset}_{process_index}.txt`에 stdout이 redirect되게 됩니다.  
	만약 빈 문자열일 경우, stdout을 redirect하지 않습니다.  
	문자열을 입력받습니다. default는 `""`입니다.  
* `storage`  
	image를 load하는 storage입니다.  
	`disk`이나 `s3`를 입력할 수 있습니다.  default는 "s3"입니다.  
* `target_dir`  
	image dataset이 disk에 저장된 root directory path입니다.  
	`storage=="disk"`인 경우에만 사용되는 argument입니다.  
	문자열을 입력받습니다. default는 `""`입니다.  
* `bucket_name`  
	AWS S3의 bucket name입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	문자열을 입력받습니다. default는 `"my-s3-bucket-name"`입니다.  
* `region_name`  
	AWS S3의 region name입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	문자열을 입력받습니다. default는 `"us-east-2"`입니다.  
* `timeout`  
	boto3를 사용해 AWS S3 bucket 내 object를 get할 때, timeout second입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	정수를 입력받습니다. default는 `1`입니다.  
* `retry`  
	boto3를 사용해 AWS S3 bucket 내 object를 get할 때, retry 시도 횟수입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	정수를 입력받습니다. default는 `0`입니다.  
* `[no-]proxy`  
	boto3를 사용해 AWS S3 bucket 내 object를 get할 때, proxy 사용 여부에 대한 flag입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	default는 `true`입니다.  
* `http-proxy`  
	boto3를 사용해 AWS S3 bucket 내 object를 get할 때, proxy를 사용할 경우의 http proxy의 주소입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	문자열을 입력받습니다. default는 `"http://proxy.example.io:10000"`입니다.  
* `https-proxy`  
	boto3를 사용해 AWS S3 bucket 내 object를 get할 때, proxy를 사용할 경우의 https proxy의 주소입니다.  
	`storage=="s3"`인 경우에만 사용되는 argument입니다.  
	문자열을 입력받습니다. default는 `"http://proxy.example.io:10000"`입니다.  

### Performance  

* Hardware  
	* CPU: AMD EPYC 32Core x 128  
	* GPU: NVIDIA A100 x 8  
	* RAM: 976GB  
* source: AWS S3  
* performance: 256M / day  
* utlization
	* CPU: 96%
	* GPU: 36%
	* Network: 1.3Gbps
	![utilization](/assets/utilization.jpg)
