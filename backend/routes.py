from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
######################################################################
# Health Check Endpoint
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Return the health status of the server"""
    return {"status": "OK"}

######################################################################
# Count Endpoint
######################################################################
@app.route("/count", methods=["GET"])
def count():
    """Return the count of songs in the database"""
    count = db.songs.count_documents({})
    return {"count": count}, 200

######################################################################
# Check connectivity to MongoDB
######################################################################

@app.route("/test-mongo", methods=["GET"])
def test_mongo():
    try:
        # Fetch a single document from the songs collection to test the connection
        song = db.songs.find_one()
        if song:
            return {"message": "Successfully connected to MongoDB!", "sample_song": parse_json(song)}, 200
        else:
            return {"message": "No data found in MongoDB!"}, 200
    except Exception as e:
        app.logger.error(f"Error connecting to MongoDB: {str(e)}")
        return {"message": "Failed to connect to MongoDB"}, 500

#MONGODB_SERVICE=localhost MONGODB_USERNAME=root MONGODB_PASSWORD=password flask run --reload --debugger

#curl -X GET -i -w '\n' localhost:5000/test-mongo

#OUTPUT#################################################################################################

# HTTP/1.1 200 OK
# Server: Werkzeug/2.1.2 Python/3.9.5
# Date: Tue, 03 Sep 2024 20:03:13 GMT
# Content-Type: application/json
# Content-Length: 319
# Connection: close

# {"message":"Successfully connected to MongoDB!","sample_song":{"_id":{"$oid":"66d76b71db6d955ff9d2a5d4"},"id":1,"lyrics":"Morbi non lectus. Aliquam sit amet diam in magna bibendum imperdiet. Nullam orci pede, venenatis non, sodales sed, tincidunt eu, felis.","title":"duis faucibus accumsan odio curabitur convallis"}}
