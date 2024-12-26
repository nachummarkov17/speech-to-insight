import os
import time
from datetime import datetime

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request
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

progress = 0
total_files = 0


def is_valid_lat_long(lat_long):
    try:
        lat, long = map(float, lat_long.split(","))
        return -90 <= lat <= 90 and -180 <= long <= 180
    except ValueError:
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_recordings")
def add_recordings():
    return render_template("add_recordings.html")


@app.route("/tools")
def tools():
    return render_template("tools.html")


@app.route("/worktable")
def worktable():
    return render_template("worktable.html")


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    global progress, total_files
    progress = 0
    total_files = 0

    if "audioFiles" not in request.files or "location" not in request.form:
        return jsonify({"message": "No files or location part in the request"}), 400

    files = request.files.getlist("audioFiles")
    location = request.form.get("location")
    case_number = request.form.get("case_number")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    # Ensure case_number is either a valid integer or None
    case_number = int(case_number) if case_number and case_number.isdigit() else None

    # Combine latitude and longitude into location
    if latitude and longitude:
        location = f"{latitude}, {longitude}"

    # Validate location
    if not is_valid_lat_long(location):
        return jsonify({"message": "Invalid latitude and longitude format"}), 400

    saved_files = []
    summaries = []
    total_files = len(files)

    for file in files:
        # Pace the API
        time.sleep(total_files / 2)
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

        print(f"SUMMARY: {summary_text}")

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
            "content_length": len(transcription.split()),
            "summary": summary_content,
            "summary_length": summary_length,
            "key_terms": key_terms,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "threat_level": threat_level,
            "location": location,
            "case_number": case_number,
            "resolved": False,
        }
        summaries.append(summary_document)

        # Insert the summary document into the database
        summary_id = mongo.db.summaries.insert_one(summary_document).inserted_id
        summary_document["_id"] = str(summary_id)

        # Update progress
        progress += 1
        time.sleep(1)  # Simulate processing time

    return (
        jsonify(
            {
                "files": saved_files,
                "summaries": summaries,
            }
        ),
        200,
    )


@app.route("/progress")
def progress_stream():
    def generate():
        global progress, total_files
        while progress < total_files:
            yield f"data: {progress}/{total_files}\n\n"
            time.sleep(1)
        yield f"data: {total_files}/{total_files}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/summaries/<id>", methods=["DELETE"])
def delete_summary(id):
    result = mongo.db.summaries.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return "", 204
    else:
        return jsonify({"message": "Summary not found"}), 404


@app.route("/api/summaries", methods=["DELETE"])
def delete_all_summaries():
    result = mongo.db.summaries.delete_many({})
    return jsonify({"message": f"{result.deleted_count} summaries deleted"}), 200


@app.route("/api/summaries/search", methods=["GET"])
def search_summaries():
    query = {}
    title = request.args.get("title")
    content = request.args.get("content")
    summary = request.args.get("summary")
    date = request.args.get("date")
    date_type = request.args.get("dateType")
    key_terms = request.args.getlist("key_terms")
    location = request.args.get("location")
    case_number = request.args.get("case_number")
    content_length = request.args.get("content_length")
    summary_length = request.args.get("summary_length")
    threat_level = request.args.get("threat_level")
    resolved = request.args.get("resolved")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if content:
        query["content"] = {"$regex": content, "$options": "i"}
    if summary:
        query["summary"] = {"$regex": summary, "$options": "i"}
    if date:
        if date_type == "before":
            query["date"] = {"$lt": date}
        elif date_type == "after":
            query["date"] = {"$gt": date}
        else:
            query["date"] = date
    if key_terms:
        regex_terms = [
            {"key_terms": {"$regex": term, "$options": "i"}} for term in key_terms
        ]
        query["$and"] = regex_terms
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if case_number:
        query["case_number"] = int(case_number)
    if content_length:
        query["content_length"] = int(content_length)
    if summary_length:
        query["summary_length"] = int(summary_length)
    if threat_level:
        query["threat_level"] = {"$regex": threat_level, "$options": "i"}
    if resolved:
        query["resolved"] = resolved.lower() == "true"
    if latitude:
        query["latitude"] = latitude
    if longitude:
        query["longitude"] = longitude

    summaries = mongo.db.summaries.find(query)
    result = []
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["date"] = str(summary["date"])
        result.append(summary)
    return jsonify(result), 200


@app.route("/api/summaries/<id>", methods=["PATCH"])
def update_summary(id):
    data = request.json
    update_fields = {
        "title": data.get("title"),
        "summary": data.get("summary"),
        "summary_length": len(data.get("summary", "").split()),
        "threat_level": data.get("threat_level"),
        "key_terms": data.get("key_terms"),
        "case_number": data.get("case_number"),
        "resolved": data.get("resolved"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    result = mongo.db.summaries.update_one(
        {"_id": ObjectId(id)}, {"$set": update_fields}
    )
    if result.matched_count == 1:
        return jsonify({"message": "Summary updated successfully"}), 200
    else:
        return jsonify({"message": "Summary not found"}), 404


@app.route("/api/summaries/<id>/case_number", methods=["PATCH"])
def update_case_number(id):
    case_number = request.json.get("case_number")
    if case_number is None:
        return jsonify({"message": "case_number is required"}), 400

    result = mongo.db.summaries.update_one(
        {"_id": ObjectId(id)}, {"$set": {"case_number": int(case_number)}}
    )
    if result.matched_count == 1:
        return jsonify({"message": "Summary updated successfully"}), 200
    else:
        return jsonify({"message": "Summary not found"}), 404


@app.route("/api/summaries/case_number", methods=["PATCH"])
def update_case_number_all():
    case_number = request.json.get("case_number")
    summary_ids = request.json.get("summary_ids")
    if case_number is None or not summary_ids:
        return jsonify({"message": "case_number and summary_ids are required"}), 400

    object_ids = [ObjectId(id) for id in summary_ids]
    result = mongo.db.summaries.update_many(
        {"_id": {"$in": object_ids}}, {"$set": {"case_number": int(case_number)}}
    )
    return jsonify({"message": f"{result.modified_count} summaries updated"}), 200


@app.route("/api/summaries/locations", methods=["GET"])
def get_summaries_locations():
    case_number = request.args.get("case_number")
    if not case_number:
        return jsonify({"message": "case_number is required"}), 400

    summaries = mongo.db.summaries.find(
        {"case_number": int(case_number)},
        {"_id": 0, "title": 1, "location": 1, "threat_level": 1},
    )
    return jsonify(list(summaries))


if __name__ == "__main__":
    app.run(debug=True, port=3000)
