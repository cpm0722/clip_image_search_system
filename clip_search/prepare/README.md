# Prepare

### Detail

CLIP Image Search Demo Application을 위한 사전 준비 과정입니다.  
[Save Embedding](/clip_search/prepare/save_embedding), [Build Index](/clip_search/prepare/build_index)의 순서로 process가 진행됩니다.  

### [Save Embedding](/clip_search/prepare/save_embedding)

disk, 또는 AWS s3 상에 존재하는 image에 대한 CLIP embedding을 추출한 후, 이를 저장하는 task입니다.  

### [Build Index](/clip_search/prepare/build_index)

추출한 CLIP embedding를 통해 HNSW(Hierarchical Navigable Small World) graph를 build하고, 이를 저장하는 task입니다.  

### Simple Usage

* [Save Embedding](/clip_search/prepare/save_embedding)
	```
	bash save_embedding/save_embedding.sh [disk|s3]
	```

* [Build Index](/clip_search/prepare/build_index)
	```
	python build_index/build_index.py [--dataset] [--index]
	```
