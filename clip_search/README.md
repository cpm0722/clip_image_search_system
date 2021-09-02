# CLIP Image Search System

### Summary

* [Prepare](/clip_search/prepare)
	* [Save Embedding](/clip_search/prepare/save_embedding): 대규모 이미지 데이터에 대한 CLIP embedding을 추출하는 task   
	* [Build Index](/clip_search/prepare/build_index): CLIP embeding을 HNSW(Hierarchical Navigable Small World) Graph로 build하는 task   
* [Server](/clip_search/server)
	* [Front Server](/clip_search/server/front): 사용자가 자연어-이미지 검색을 수행 결과를 실시간으로 확인할 수 있도록 하는 server  
	* [Middle Server](/clip_search/server/middle): 다수의 search server에 대한 Sharding을 포함, server 간 communication을 총괄하는 server  
	* [Inference Server](/clip_search/server/inference): CLIP에 대해 text inference를 수행하는 server  
	* [Search Server](/clip_search/server/search): approximated k-nn search(HNSW)를 수행하는 server  
