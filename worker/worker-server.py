#
# Worker server
#
import pickle
import platform
import io
import os
import sys
import pika
import redis
import hashlib
import json
import requests
import time
import random

from flair.models import TextClassifier
from flair.data import Sentence


classifier = TextClassifier.load('sentiment')

hostname = platform.node()

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print(f"Connecting to rabbitmq({rabbitMQHost}) and redis({redisHost})")

##
## Set up redis connections
##
db = redis.Redis(host=redisHost, db=1)                                                                           

##
## Set up rabbitmq connection
##
rabbitMQ = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()

result = rabbitMQChannel.queue_declare(queue='toWorker')
# rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')
# rabbitMQChannel.queue_bind(exchange='logs', queue=result.method.queue)

print("Waiting for Messages")
print("ready for checkout? ")

def callback(ch, method, properties, body):
    print("Received %r" % body.decode())
    time.sleep(body.count(b'.'))
    currSentence = body.decode()
    ch.basic_ack(delivery_tag=method.delivery_tag)
    sentence = Sentence(currSentence)
    # db.set(currSentence, str(sentence.labels))
    print("Set key : " + currSentence + "in db to : " + str(sentence.labels) )
#     # make example sentence

#     print("Done")

rabbitMQChannel.basic_consume(queue='toWorker', on_message_callback=callback)

rabbitMQChannel.start_consuming()
