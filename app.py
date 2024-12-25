import os
from datetime import datetime

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename

from speech_transcriber import transcribe_audio
from summarizer import summarize_text

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
    summaries = []

    for file in files:
        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        saved_files.append(filename)

        # Transcribe the audio file
        transcription = transcribe_audio(file_path)

        # Summarize the transcribed text
        summary_text = summarize_text(transcription)

        # Extract summary details from the summary text
        summary_lines = summary_text.split("\n")
        title = summary_lines[0].strip("[]")
        summary_content = summary_lines[1].strip("[]")
        summary_length = int(summary_lines[3].split(": ")[1].split()[0])
        threat_level = summary_lines[4].split(": ")[1].rstrip("]")
        key_terms = summary_lines[5].strip("[]").split(", ")

        # Create the summary document
        summary_document = {
            "title": title,
            "content": transcription,
            "contentLength": len(transcription.split()),
            "summary": summary_content,
            "summaryLength": summary_length,
            "key_terms": key_terms,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "threat_level": threat_level,
        }
        summaries.append(summary_document)

        # Insert the summary document into the database
        summary_id = mongo.db.summaries.insert_one(summary_document).inserted_id
        summary_document["_id"] = str(summary_id)

    return (
        jsonify(
            {
                "files": saved_files,
                "summaries": summaries,
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
        # Ensure the date is treated as a string
        summary["date"] = str(summary["date"])
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
        summary["date"] = str(summary["date"])
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
        summary["date"] = str(summary["date"])
        result.append(summary)
    return jsonify(result), 200


@app.route("/api/summaries/date_range", methods=["GET"])
def get_summaries_by_date_range():
    start_date_str = request.args.get("start")
    end_date_str = request.args.get("end")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    query = {"date": {"$gte": start_date, "$lte": end_date}}
    summaries = mongo.db.summaries.find(query)
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["date"] = str(summary["date"])
        result.append(summary)
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True, port=3000)
