#!/bin/sh
#
# Sample queries using Curl rather than rest-client.py
#

#
# Use localhost & port 5000 if not specified by environment variable REST
#
REST=${REST:-"localhost:80"} ## Repalce with public IP for google cloud > kubectl decribe ingress rest-ingress
##Create and delete cluster on google cloud or it will cost money
echo "Send sentences to analyze"
curl -X POST -H "Content-Type: application/json" HTTP://$REST/apiv1/analyze -d@- << __EOF__
{
    "model" : "sentiment",
    "sentences" : [
        "Happy Thanksgiving",
        "This thing sucks",
        "I don't like that one"
    ],
    "callback" : {
        "url" : "http://localhost:80",
        "data" : { "some": "arbitrary", "data" : "to be returned" }
    }
}
__EOF__
echo ""

echo "Waiting for items to be processed...."
sleep 2;
echo "====================="
echo "Dump cache..."
curl -X GET -H "Content-Type: application/json" "HTTP://$REST/apiv1/cache/sentiment"
echo ""

echo "====================="
echo "Retrieve specific sentences"
curl -X GET -H "Content-Type: application/json" HTTP://$REST/apiv1/sentence -d@- << __EOF__
{
    "model" : "sentiment",
    "sentences" : [
        "I think this is a good thing",
        "This thing sucks",
        "I don't like that one"
    ] 
}
__EOF__
echo ""
echo "====================="
echo "Retrieve non-analyzed sentences along with analyzed sentence"
curl -X GET -H "Content-Type: application/json" HTTP://$REST/apiv1/sentence -d@- << __EOF__
{
    "model" : "sentiment",
    "sentences" : [
        "I don't think this one exists",
        "I think this is a good thing"
    ] 
}
__EOF__