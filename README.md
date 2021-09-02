# CLIP Image Search System

### Summary

OpenAI에서 공개한 [CLIP](https://github.com/openai/CLIP)을 활용한 자연어-이미지 검색 시스템입니다.  
image dataset은 imagenet21k, CC12M, openimages 등 public dataset에 더해 web에서 crawling한 image들로 구성되어 전체 약 **600M**개의 image dataset을 구축했습니다.  
**600M** 이상의 image에 대해 HNSW(Hierarchical Navigable Small World) algorithm을 사용해 cosine similarity 기반의 appriximated nearest neighbor vector search를 수행합니다.  
이 때, Sharding을 구현해 다수의 server에 data를 분산 저장함으로써 대규모 data에 대해서도 균등한 성능을 유지합니다.  
최종적으로 **300ms** 미만의 latency, **95%** 이상의 recall을 보장합니다.  

### Example
몇몇 예제 query에 대한 검색 결과입니다.  

* query text: "a Korean meal"  
  <img src="/assets/a_Korean_meal.jpg" width="70%">
* query text: "해변을 달리는 강아지"  
  <img src="/assets/a_dog_running_on_the_beach.jpg" width="70%">
* query text: "a seaside overlooking from the sky" (compare with Google Image Search)  
  <img src="/assets/a_seaside_overlooking_from_the_sky.jpg" width="100%">
