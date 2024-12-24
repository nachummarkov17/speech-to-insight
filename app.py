import os
from datetime import datetime

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename

from recording_to_text import transcribe_audio

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["UPLOAD_FOLDER"] = "uploads"
mongo = PyMongo(app)

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_recordings")
def add_recordings():
    return render_template("add_recordings.html")


@app.route("/check_ai_summary")
def check_ai_summary():
    return render_template("check_ai_summary.html")


@app.route("/tools")
def tools():
    return render_template("tools.html")


@app.route("/worktable")
def worktable():
    return render_template("worktable.html")


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audioFiles" not in request.files:
        return jsonify({"message": "No files part in the request"}), 400

    files = request.files.getlist("audioFiles")
    saved_files = []
    transcriptions = []

    for file in files:
        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        saved_files.append(filename)

        # Transcribe the audio file
        transcription = transcribe_audio(file_path)
        transcriptions.append({"filename": filename, "transcription": transcription})

    return (
        jsonify(
            {
                "message": "Files successfully uploaded",
                "files": saved_files,
                "transcriptions": transcriptions,
            }
        ),
        200,
    )


@app.route("/api/summaries", methods=["POST"])
def create_summary():
    data = request.json
    if "date" in data:
        try:
            data["date"] = datetime.strptime(data["date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400
    summary_id = mongo.db.summaries.insert_one(data).inserted_id
    summary = mongo.db.summaries.find_one({"_id": ObjectId(summary_id)})
    summary["_id"] = str(summary["_id"])
    summary["date"] = summary["date"].strftime("%Y-%m-%d")
    return jsonify(summary), 201


@app.route("/api/summaries", methods=["GET"])
def get_summaries():
    summaries = mongo.db.summaries.find()
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["date"] = summary["date"].strftime("%Y-%m-%d")
        result.append(summary)
    return jsonify(result), 200


@app.route("/api/summaries/<id>", methods=["DELETE"])
def delete_summary(id):
    result = mongo.db.summaries.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return "", 204
    else:
        return jsonify({"message": "Summary not found"}), 404


@app.route("/api/summaries/date_search", methods=["GET"])
def search_summaries_by_date():
    date_str = request.args.get("date")
    filter_type = request.args.get("type", "equal")

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    if filter_type == "before":
        query = {"date": {"$lt": date}}
    elif filter_type == "after":
        query = {"date": {"$gt": date}}
    else:
        query = {"date": date}

    summaries = mongo.db.summaries.find(query)
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["date"] = summary["date"].strftime("%Y-%m-%d")
        result.append(summary)
    return jsonify(result), 200


@app.route("/api/summaries/key_term_search", methods=["GET"])
def search_summaries_by_key_terms():
    key_terms = request.args.getlist("key_terms")
    if not key_terms:
        return jsonify({"message": "No key_terms provided."}), 400

    regex_terms = [
        {"key_terms": {"$regex": term, "$options": "i"}} for term in key_terms
    ]
    query = {"$and": regex_terms}
    summaries = mongo.db.summaries.find(query)
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["date"] = summary["date"].strftime("%Y-%m-%d")
        result.append(summary)
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
