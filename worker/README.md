# Sentiment Analysis Worker

The steps you need to take:

+ Develop a Python program that listens to the `toWorkers` RabbitMQ exchange, receives a message and determine the sentiment of each sentence.
+ Create a Docker image that can execute the sentiment analysis software, run RabbitMQ clients and has access to a remote Redis database
## Creating a worker image
The worker will use the [flair sentiment analysis software](https://github.com/flairNLP/flair) software. This is an open-source natural language processing library that has Python bindings and good documentation. The software distribution requires Python 3.6 or above; installing Flair is as simple as executing:
```
pip install flair
```
Installing flair installs many packages, produces a ~3.5GB container image. It takes a while to upload that to e.g. the `docker.io` registry. To save time, I've prepare a pre-built Flair installation at `dirkcgrunwald/flair` that is the container resulting from this Dockerfile:
```
FROM python:3.6-slim
LABEL MAINTAINER="dirk grunwald <grunwald@colorado.edu>"

RUN pip install flair
``` 
The resulting image `dirkcgrunwald/flair:latest` is 3.5GB in size. You can, but are not required to, use this as the base image for the image containing your worker code. Recall that you can extend a Docker image using `FROM`, then adding additional files and over-riding the `CMD` or `RUN` commands. That means you do *not* need to build the basic `flair` Docker container yourself and when you "push" your image to Docker hub, you should have to upload very little data because my base image has already been uploaded.
## Program to do sentiment analysis

You will need two RabbitMQ exchanges.
+ A `topic` exchange called `logs` used for debugging and logging output
+ A `direct` exchange called `toWorker` used by the REST API to send sentiment analysis tasks to the worker

You can use whatever method you like to get data from the REST API to the worker, but we do want you to use RabbitMQ because it enables reliable messaging. For example, you could create a Python datatype including the sentiment task, then [`pickle` the image](https://stackoverflow.com/questions/30469575/how-to-pickle-and-unpickle-to-portable-string-in-python-3) and send it via RabbitMQ or you can just send e.g. a JSON text message. My solution just sends JSON strings.

Although sentiment analysis is reasonably fast (~10-500ms), you should implement a *cache* of saved analysis using Redis, a Key-Value store. Redis supports a [number of datatypes including lists and sets](https://redis.io/topics/data-types); you can read more about [the Python interface](https://github.com/andymccurdy/redis-py). My solution used *sets* because I wanted to support caching the results from different sentiment classifiers.

The worker should extract the set of sentences to process from the request, check if the sentence has already been processed using the Redis cache and, if not, perform the sentiment analysis using the specified classification model and store it in the Redis database. You should correct handle the fact that the same sentence could be classified using different *classifier models*. If you don't want to cache multiple results for the same sentence, you can just mark what classifier model was used by the cache result and recompute it if a different one is requested. Or, you can [use the set datatype](https://redis.io/commands#set) operations, including *sadd* and *smembers*, to store multiple results. You'll need to use the same mechanism in your REST api server since that will retrieve results from Redis too.

Once the database has been updated or you determine nothing needs to be done you should then `acknowledge` the RabbitMQ message. You should only acknowledge it after you've processed the full request which may contain many sentences.

In addition, if the `toWorker` request indicates that a *webhook callback* should be used, you should issue an HTTP POST request passing in the payload portion of the callback. You [can use the Python requests library](https://docs.python-requests.org/en/latest/user/quickstart/#make-a-request) to make that request. You don't need to do anything if the request fails, but you should be aware the request may fail.

## Sentiment Analysis
The [Flair library has documentation on how to run sentiment analysis](https://github.com/flairNLP/flair/blob/master/resources/docs/TUTORIAL_2_TAGGING.md#tagging-with-pre-trained-text-classification-models). The basic steps are:
```
from flair.models import TextClassifier
classifier = TextClassifier.load('sentiment')
sentence = Sentence("enormously entertaining for moviegoers of any age.")
classifier.predict(sentence)
print(sentence.to_dict('sentiment'))
```
but you will need to specify the classifier (*e.g.* 'sentiment', ''sentiment-fast', *etc*) and you probably want to use *e.g.* `to_dict('sentiment')` to return a Python dictionary (similar to a JSON dictionary). You can store a JSON version of that dictionary in the Redis database, possibly augmenting it to indicate the text classifier model.

## Debugging Support

At each step of your processing, you should log debug information using the `topic` queue and `[hostname].worker.debug`. When you've added the data to the database, you *must* log that as `[hostname].worker.info`, substituting the proper worker name.

When installing the `pika` library used to communicate with `rabbitmq`, you should use the `pip` or `pip3` command to install the packages. My solution used the following Python packages in addition to `flair`
```
sudo pip3 install --upgrade pika redis requests
```

## Suggested Development Steps

When you actually run the text classifier, the existing 2.5GByte model will be downloaded from Germany. If you do this in a container or pod, this model will be repeatedly downloaded. This takes a while and it slows down your debug-edit cycle. If you do this on your laptop instead of in a container the downloaded model will be saved in your home directory.

Thus, we recommend that:
* Install `flair` on your laptop using `pip3 install flair`
* Do your development by running your `worker-server.py` on your laptop natively and not in a container or pod. This means you'll download the 2.5GB data file once.
* Deploy Redis and Rabbitmq and the use the `kubectl port-forward` mechanism listed in the [corresponding README.md](../redis/README.md) file to expose those services on your local machine. We've [provided a script `deploy-local-dev.sh`](../deploy-local-dev.sh) for that purpose.
* Now that you are port-forwarding during development, you can run `worker-server.py` on your laptop and it will find the Redis/Rabbitmq ports on the localhost. 
* But, when you deploy your solution in Kubernetes, you'll need to tell `worker-server.py` what hosts to use when deployed; this should be done using environment variables in the deployment specification.
* Use the provided `log_info` and `log_debug` routines that write to the `logs` topic to simplify your development. You won't be able to figure out what is going on without logs. We've provided template code for that.

Lastly, you should construct a program to send a sample request to your worker. We've [included one in send-request.py](./send-request.py) that uses the message format that my solution uses.

Following this process, you can debug the use of the `flair` library and the interface to redis and rabbitmq. When you've got it working, you can then deploy to Kubernetes.
