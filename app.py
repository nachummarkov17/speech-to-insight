from bson.objectid import ObjectId
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

@app.route("/api/summaries", methods=["POST"])
def create_summary():
    data = request.json
    summary_id = mongo.db.summaries.insert_one(data).inserted_id
    summary = mongo.db.summaries.find_one({"_id": ObjectId(summary_id)})
    summary["_id"] = str(summary["_id"])
    return jsonify(summary), 201

@app.route("/api/summaries", methods=["GET"])
def get_summaries():
    summaries = mongo.db.summaries.find()
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        result.append(summary)
    return jsonify(result), 200

@app.route("/api/summaries/<id>", methods=["DELETE"])
def delete_summary(id):
    result = mongo.db.summaries.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return "", 204
    else:
        return jsonify({"message": "Summary not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=3000)
