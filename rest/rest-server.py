##
from flask import Flask, request, Response, jsonify
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
app = Flask(__name__)
##
## Configure test vs. production
##
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

@app.route('/apiv1/analyze', methods=['POST'])  #store sentences db
def analyze():
    r = request  ##ADD SENTENCES TO RABBITMQ Q  
    r2 = r.get_json()
    sentences = r2['sentences']
    for curSentence in sentences: 

    # rabbitMQChannel.basic_publish(exchange='', routing_key='toWorker', body=sentences)
        rabbitMQChannel.basic_publish(exchange='',
                         routing_key='toWorker',
                         body=curSentence)
        print(" [x] Sent %r" % curSentence)
    return {"action": "queued"}


# route http posts to this method
@app.route('/apiv1/cache/sentiment', methods=['GET'])# get sentences from db cache AND sentence don't interact with the worker at all. 
###updaate db in the worker 
def cache():
    # r = request.get_json()
    # print("In CACHE ", r)
    keysLst = db.keys()
    returnLst = []
    # print("DB: ", db.keys())
    for key in keysLst:
        # result  = {"model" : "sentiment", 
        #             "result" : {
        #                 "entities":[],
        #                  "labels": [],
                            # "text" : key
        #             } 
        
        currKey = str(key.decode())
        # print("Keyx : " ,  str(key.decode()))
        print(db.get(str(currKey))) ##WHY IS THIS NOT WORKING WHEN
        if db.get(str(currKey)) != None:
            currVal = db.get(currKey)
            # print("Current db entry: ", currVal)
            workString = str(currVal.decode())
            workString = workString[1:-1]
            lst = workString.split(' ')
            # print(workString.split(' '))
            result  = {"model" : "sentiment", 
                    "result" : {
                        "entities":[],
                         "labels": [
                             {
                             "confidence" : str(lst[1]),
                             "value" : str(lst[0])
                             }
                         ],
                            "text" : currKey
                    }
            } 
            returnLst.append(result)
            # returnLst.append({currVal})
    return {"model": "sentiment", "sentences" : returnLst}
    # return db.get('This thing sucks')


@app.route('/apiv1/sentence', methods=['GET'])
def sentence():
    returnLst = []
    r = request.get_json()
    sentences = r['sentences']
    print(sentences)
    for currSent in sentences: 
        print("Keyx : " ,  str(currSent))

        if db.get(currSent):
            
            result = db.get(currSent)
            workStr = result.decode()
            workStr = workStr[1:-1].split(' ')
            result2  = {"model" : "sentiment", 
                    "result" : {
                        "entities":[],
                         "labels": [
                             {
                             "confidence" : str(workStr[1]),
                             "value" : str(workStr[0])
                             }
                         ],
                            "text" : currSent
                    }
            } 
            print(result.decode())
            returnLst.append(result2)
        if db.get(currSent) == None: 
            returnLst.append({currSent :  "Not analyzed yet"})
    return {"model" : 'sentiment', "sentences" :returnLst}
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