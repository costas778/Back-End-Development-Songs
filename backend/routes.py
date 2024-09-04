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

# {"message":"Successfully connected to MongoDB!","sample_song":{"_id":{"$oid":"66d76b71db6d955ff9d2a5d4"},
#"id":1,"lyrics":"Morbi non lectus. Aliquam sit amet diam in magna bibendum imperdiet. Nullam orci pede,
# venenatis non, sodales sed, tincidunt eu, felis.","title":"duis faucibus accumsan odio curabitur convallis"}}

######################################################################
# GET /Song Endpoint
######################################################################

@app.route("/song", methods=["GET"])
def songs():
    try:
        # Retrieve all songs from the MongoDB collection
        songs_list = list(db.songs.find({}))
        # Return the list of songs in JSON format with a status code 200
        return {"songs": parse_json(songs_list)}, 200
    except Exception as e:
        app.logger.error(f"Error fetching songs from MongoDB: {str(e)}")
        return {"message": "Failed to fetch songs"}, 500

######################################################################
# GET /Song/id Endpoint
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Find a song by its id
        song = db.songs.find_one({"id": id})
        if song:
            # If the song is found, return it as JSON with status 200
            return parse_json(song), 200
        else:
            # If the song is not found, return a 404 error message
            return {"message": f"Song with id {id} not found"}, 404
    except Exception as e:
        app.logger.error(f"Error fetching song with id {id} from MongoDB: {str(e)}")
        return {"message": "Failed to fetch song"}, 500

######################################################################
# POST /Song Endpoint
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    # Extract the song data from the request body
    song = request.get_json()

    # Check if a song with the same id already exists
    existing_song = db.songs.find_one({"id": song["id"]})
    
    if existing_song:
        # If the song already exists, return a 302 FOUND response
        return jsonify({"Message": f"song with id {song['id']} already present"}), 302

    # Insert the new song into the database
    result = db.songs.insert_one(song)

    # Return a 201 CREATED response with the inserted id
    return jsonify({"inserted id": str(result.inserted_id)}), 201

######################################################################
# PUT /Song Endpoint
######################################################################

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    # Extract the updated song data from the request body
    updated_song = request.get_json()

    # Find the song in the database
    existing_song = db.songs.find_one({"id": id})
    
    if not existing_song:
        # If the song does not exist, return a 404 NOT FOUND response
        return jsonify({"message": "song not found"}), 404

    # Update the song in the database
    result = db.songs.update_one({"id": id}, {"$set": updated_song})

    if result.modified_count > 0:
        # If the song was updated, return the updated song
        return jsonify({"_id": str(existing_song["_id"]), "id": id, **updated_song}), 201
    else:
        # If the song was found but nothing was updated, return a 200 OK response
        return jsonify({"message": "song found, but nothing updated"}), 200

######################################################################
# DELETE /Song Endpoint
######################################################################

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    # Attempt to delete the song from the database
    result = db.songs.delete_one({"id": id})

    if result.deleted_count == 0:
        # If no song was deleted, return a 404 NOT FOUND response
        return jsonify({"message": "song not found"}), 404

    # If the song was successfully deleted, return a 204 NO CONTENT response
    return '', 204

