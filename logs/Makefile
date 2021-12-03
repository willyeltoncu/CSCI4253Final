VERSION=v3
DOCKERUSER=dirkcgrunwald

#
# You should probably update the docker.io user if you update this
#

build:
	docker build -f Dockerfile -t sentiment-logs  .
push:
	docker tag logs  $(DOCKERUSER)/sentiment-logs:$(VERSION)
	docker push $(DOCKERUSER)/sentiment-logs:$(VERSION)
	docker tag logs  $(DOCKERUSER)/sentiment-logs:latest
	docker push $(DOCKERUSER)/sentiment-logs:latest