VERSION=v4
DOCKERUSER=dirkcgrunwald

build:
	docker build -f Dockerfile-rest -t sentiment-rest .

push:
	docker tag sentiment-rest $(DOCKERUSER)/sentiment-rest:$(VERSION)
	docker push $(DOCKERUSER)/sentiment-rest:$(VERSION)
	docker tag sentiment-rest $(DOCKERUSER)/sentiment-rest:latest
	docker push $(DOCKERUSER)/sentiment-rest:latest
