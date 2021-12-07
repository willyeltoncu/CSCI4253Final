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
    return{"Number of items in stock " : str(len(db.keys()))}
    # r = request  ##ADD SENTENCES TO RABBITMQ Q  
    # r2 = r.get_json()
    


# route http posts to this method
@app.route('/apiv1/populate', methods=['POST'])# get sentences from db cache AND sentence don't interact with the worker at all. 
###updaate db in the with prices
def populate():
    r = request.get_json()
    # print(r)
    for item in r['items']:
        currItem = json.dumps(item)
        # print("Send this : " , currItem)
        rabbitMQChannel.basic_publish(exchange='',
                         routing_key='toWorker',
                         body=currItem)
        print(" [x] Sent %r" % currItem)
    return {"database": "populated"}

@app.route('/apiv1/checkout', methods=['POST'])
def checkout():
    print("We hope you found everything you were looking for.")
    r = request.get_json()
    print(r)
    totalPrice = 0.0
    recipt = []
    for item in r['order']:
        currItem = list(item.keys())[0] 
        currQuant = list(item.values())[0]
        print(currItem, currQuant)
        if db.get(currItem):
            addition = float(currQuant) * float(db.get(currItem))
            totalPrice += addition
            recipt.append(currItem + " -- " + str(addition))
        else: 
            recipt.append(currItem + str( " -- OUT OF STOCK (0.00)"))
    ##Order processing maybe message to the worker 
    return{"Order Completed!" : [
        {"Recipt" : recipt},
        {"Total" : str(totalPrice)}
        ]}
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