# REST API and interface

You must create a rest-server deployment, service and ingress that makes the specified REST api externally available.

You must provide a `rest-server.py` that implements a Flask server that responds to the routes below. 
We have provided example REST API queries implemented using CURL in `sample-requests.sh` and using Python in `sample-requests.py`

The REST routes are:
+ /apiv1/analyze[POST] - analyze the JSON list `sentences` with model `model` and perform a sentiment analysis on the list of sentences provided in the JSON payload following [the code guidelines in the Flair tutorials](https://github.com/flairNLP/flair/blob/master/resources/docs/TUTORIAL_2_TAGGING.md#tagging-with-pre-trained-text-classification-models). When the analysis is completed the specified `callback` may be called but does not need to succeed.
+ /apiv1/cache/<model> [GET] - dump the cached entries from the Redis database processed with model `model`
+ /sentiment/sentence[GET] - retrieve the sentiment analysis for the specified sentences if they exist in the database 

Sample queries using CURL are in `sample-requests.sh`. The same queries using the Python `requests` API are in `sample-requests.py`.

Sample output from my solution using the examples in `sample-requests.py` are below. The responses from `sample-requests.sh` should be identical except not be pretty-printed.
```
Response to http://34.132.155.89/apiv1/analyze request is
{
    "action": "queued"
}
Response to http://34.132.155.89/apiv1/cache/sentiment request is
{
    "model": "sentiment",
    "sentences": [
        {
            "model": "sentiment",
            "result": {
                "entities": [],
                "labels": [
                    {
                        "confidence": 0.999980092048645,
                        "value": "NEGATIVE"
                    }
                
                ],
                "text": "I don't like that one"
            }
        },
        {
            "model": "sentiment",
            "result": {
                "entities": [],
                "labels": [
                    {
                        "confidence": 0.9900237917900085,
                        "value": "POSITIVE"
                    }
                ],
                "text": "I think this is a good thing"
            }
        },
        {
            "model": "sentiment",
            "result": {
                "entities": [],
                "labels": [
                    {
                        "confidence": 0.9999688863754272,
                        "value": "NEGATIVE"
                    }
                ],
                "text": "This thing sucks"
            }
        }
    ]
}
Response to http://34.132.155.89/apiv1/sentence request is
{
    "model": "sentiment",
    "sentences": [
        {
            "analysis": {
                "model": "sentiment",
                "result": {
                    "entities": [],
                    "labels": [
                        {
                            "confidence": 0.9900237917900085,
                            "value": "POSITIVE"
                        }
                    ],
                    "text": "I think this is a good thing"
                }
            },
            "sentence": "I think this is a good thing"
        },
        {
            "analysis": {
                "model": "sentiment",
                "result": {
                    "entities": [],
                    "labels": [
                        {
                            "confidence": 0.9999688863754272,
                            "value": "NEGATIVE"
                        }
                    ],
                    "text": "This thing sucks"
                }
            },
            "sentence": "This thing sucks"
        },
        {
            "analysis": {
                "model": "sentiment",
                "result": {
                    "entities": [],
                    "labels": [
                        {
                            "confidence": 0.999980092048645,
                            "value": "NEGATIVE"
                        }
                    ],
                    "text": "I don't like that one"
                }
            },
            "sentence": "I don't like that one"
        }
    ]
}
```

##
## Rabbit MQ timeout
##
RabbitMQ has a [time out mechanism](https://stackoverflow.com/questions/36123006/rabbitmq-closes-connection-when-processing-long-running-tasks-and-timeout-settin) used to monitor connections;
if your REST server isn't receiving requests, it will eventually time out and
by default, the connection will drop and your program will get an exception at that time
which will kill your web server. You'll see your pods in an endless crashloop. 
To prevent this, you should open connections AFTER you receive your REST queries, for each rest query, and then close the channel when you're finished with that request.


### Development Steps
You will need two RabbitMQ exchanges.
+ A `topic` exchange called `logs` used for debugging and logging output
+ A `direct` exchange called `toWorker` used by the REST API to send images to the worker

You should use the topic exchange for debug messages with the topics `[hostname].rest.debug` and `[hostname].rest.info`, substituting the proper hostname. You can include whatever debugging information you want, but you must include a message for each attempted API call and the outcome of that call (successful, etc).

You may find it useful to create a `logs` container and deployment that listen to the logs and dumps them out to `stderr` so you can examine them using `kubectl logs..`.

When installing the `pika` library used to communicate with `rabbitmq`, you should use the `pip` or `pip3` command to install the packages in your container. The solution code uses the following packages:
```
sudo pip3 install --upgrade pika redis jsonpickle requests flask
```

## Deploying an ingress
## Deploy an `ingress` to publish our web server

Although an ingress is a standard Kubernetes network component, the specific implementation depends on the Kubernetes system you're using.  Once you've developed your service, you should deploy it on Google Container Engine (GKE). The steps to create a "ingress" on GKE are slightly different than the steps for the stand-alone Kubernetes development environment [discussed in the Kubernetes tutorial](https://github.com/cu-csci-4253-datacenter/kubernetes-tutorial/tree/master/05-guestbook). In that example, you [install an ingress extension based on nginx](https://kubernetes.github.io/ingress-nginx/deploy/#docker-for-mac) and then configure the ingress to forward from the host IP address to the specific service you want to access. The options below document each possible option for testing and deployment:

### If you're using Docker Desktop
This example uses the [kubernetes-ingress](https://github.com/nginxinc/kubernetes-ingress/blob/master/examples/complete-example/cafe-ingress.yaml) which works well for Docker Desktop. You must install the ingress controller software using ( e.g. )
```
> kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.4/deploy/static/provider/cloud/deploy.yaml
```
as shown at [the directions on deploying this for Docker Desktop](https://kubernetes.github.io/ingress-nginx/deploy/#docker-desktop). It takes a moment for the Ingress controller that you installed to actually be ready, so if the steps below don't work, wait a moment and try again.

### If you're using GKE
For Google Kubernetes Engine (GKE) you follow basically the same steps:
```
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole cluster-admin \
  --user $(gcloud config get-value account)
```
and then deploy the ingress:
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.4/deploy/static/provider/cloud/deploy.yaml
```

### Using a GKE load balancer

For GKE, you [can use a "load balancer" as the ingress as described in this tutorial](https://cloud.google.com/kubernetes-engine/docs/how-to/load-balance-ingress#gcloud). In general, Google's load balancer can accept connections across multiple datacenters and direct them to your Kubernetes cluster. You first need to enable the load balancer functionality (assuming your cluster is named `mykube`) using:
```
gcloud container clusters update mykube --update-addons=HttpLoadBalancing=ENABLED
```

You can then use [create an ingress that directs web connections to your rest-service using the example from the tutorial](https://cloud.google.com/kubernetes-engine/docs/how-to/load-balance-ingress#creating_an_ingress). The main difference is that you need to specify:
```
  annotations:
    kubernetes.io/ingress.class: "gce"
```

The GKE load balancer [needs your service to use a specific kind of service called a `NodePort`](https://cloud.google.com/kubernetes-engine/docs/how-to/load-balance-ingress#creating_a_service). You can add that to your service spec by putting
```
spec:
  type: NodePort
```
in the service YAML file and restarting your service.

In addition, the GKE load balancer checks for the "health" of your service -- this means that you need to respond to requests to `/` with a positive response. I added the following route:
```
@app.route('/', methods=['GET'])
def hello():
    return '<h1> Sentiment Server</h1><p> Use a valid endpoint </p>'
```

Once you've created the load-balancer, you can find the IP address using *e.g.*
```
kubectl get ingress rest-ingress --output yaml
```
and then access the endpoint using the IP address at the end of the output. It should look like:
```
....
status:
  loadBalancer:
    ingress:
    - ip: 34.120.45.70
```
You can check if things are working by sending requests and looking at the output of your `logs` pod or the response you get.

If you have trouble getting your service to work, use
```
kubectl describe ingress rest-ingress
```
and you'll see error messages and diagnostics like this:
```
> kubectl describe ingress rest-ingress
Name:             rest-ingress
Namespace:        default
Address:          34.120.45.70
Default backend:  default-http-backend:80 (10.0.0.9:8080)
Rules:
  Host        Path  Backends
  ----        ----  --------
  *           
              /hello   hello-world:60000 (10.0.0.10:50000,10.0.1.7:50000,10.0.2.7:50000)
              /*       rest-service:5000 (10.0.2.15:5000)
Annotations:  ingress.kubernetes.io/backends:
                {"k8s-be-30496--28fa4eee16792bba":"HEALTHY","k8s-be-30815--28fa4eee16792bba":"HEALTHY","k8s-be-30914--28fa4eee16792bba":"HEALTHY"}
              ingress.kubernetes.io/forwarding-rule: k8s2-fr-pxfi3hd8-default-rest-ingress-zo9uwq5a
              ingress.kubernetes.io/target-proxy: k8s2-tp-pxfi3hd8-default-rest-ingress-zo9uwq5a
              ingress.kubernetes.io/url-map: k8s2-um-pxfi3hd8-default-rest-ingress-zo9uwq5a
              kubernetes.io/ingress.class: gce
Events:
  Type    Reason  Age   From                     Message
  ----    ------  ----  ----                     -------
  Normal  ADD     46m   loadbalancer-controller  default/rest-ingress
  Normal  CREATE  45m   loadbalancer-controller  ip: 34.120.45.70
```
It can take a while for the status of the connections to switch from "Unknown" to "HEALTHY". If that isn't happening, check that you've added the `/` route to your Flask server and try connecting to the IP address.

If you can't get this to work, just use your local Kubernetes setup during your grading interview.
