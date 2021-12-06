##
from flask import Flask, request, Response, jsonify
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
import pandas as pd 
app = Flask(__name__)
##
## Configure test vs. production
# ##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
db = redis.Redis(host=redisHost, db=1)   ##                                                                        

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))
rabbitMQ = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()
rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')

rabbitMQChannel.queue_declare(queue='toWorker')
# rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')

infoKey = f"{platform.node()}.worker.info"

# rabbitMQChannel.basic_publish(exchange='logs', routing_key=infokey, body=message)

##RABBITMQ PUBLISH/SUBSCRIBE LOOK UP 
## QUERE FOR WORKER-REST

@app.route('/apiv1/load', methods=['POST'])  #store sentences db
def load():
    print("LOAD")
    data = pd.read_csv("data.csv")
    mydata = data[ ["brand", "price"] ] # only those columns
    mydata.to_json(orient="records") # produces a string of your output which you can dump to a file
    print(mydata)
    pass


@app.route('/apiv1/stock', methods=['GET'])  #print out all in stock items
def message():
    print("Here are all of our instock items : ")
    for i in db.keys():
        print(str(i))
    return{"Number of items " : str(len(db.keys()))}
    # r = request  ##ADD SENTENCES TO RABBITMQ Q  
    # r2 = r.get_json()
    


# route http posts to this method
@app.route('/apiv1/populate', methods=['POST'])# get sentences from db cache AND sentence don't interact with the worker at all. 
###updaate db in the with prices
def populate():
    r = request.get_json()
    print(r)
    for item in r['items']:
        print("Item type / Brand : " , item['brand'])
        print("Item Cost in USD : " , item['price'])
        db.set(item['brand'], item['price'])
    for i in db.keys():
        # db.set(brand, price)
        print(db[i]) #Possibly add to the db within the worker just to include rabbitMQ 
    # sentences = r2['sentences']
    # for curSentence in sentences: 

    # # rabbitMQChannel.basic_publish(exchange='', routing_key='toWorker', body=sentences)
    #     rabbitMQChannel.basic_publish(exchange='',
    #                      routing_key='toWorker',
    #                      body=curSentence)
    #     print(" [x] Sent %r" % curSentence)
    return {"yes": "yea"}

@app.route('/apiv1/checkout', methods=['POST'])
def checkout():
    print("We hope you found everything you were looking for.")
    ##Order processing maybe message to the worker 
    return{"CO" : "WIP"}
# start flask app
app.run(host="0.0.0.0", port=5000)


# def log_debug(message, key=debugKey):
#     print("DEBUG:", message, file=sys.stdout)
#     rabbitMQChannel.basic_publish(
#         exchange='logs', routing_key=key, body=message)
# def log_info(message, key=infoKey):
#     print("INFO:", message, file=sys.stdout)
#     rabbitMQChannel.basic_publish(
#         exchange='logs', routing_key=key, body=message)