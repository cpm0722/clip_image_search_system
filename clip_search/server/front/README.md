# Front Server

### Summary  
front server입니다.  
사용자가 web page에 입력한 text query를 middle server에 전달하고, 검색 결과인 image들을 받아 출력합니다.  

### Usage  

```
python front.py [--wsgi] [--gunicorn-num-workers]
```

* `wsgi`  
	flask의 WSGI를 선택합니다. 
	`\"gunicorn\"`이나 `\"waitress\"`를 입력할 수 있습니다. default는 `\"gunicorn\"`입니다.  
* `gunicorn-num-workers`  
	flask의 WSGI로 `\"gunicorn\"`을 선택했을 때의 process 개수입니다.  
	정수을 입력받습니다. default는 `28`입니다.  
