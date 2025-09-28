import os
import boto3
import mimetypes
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
# import requests
from flask_cors import CORS
from io import BytesIO

load_dotenv()

app = Flask(__name__)

# Load AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

# Initialize the S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

@app.route("/upload", methods=["POST"])
def upload_file():
    """Endpoint to upload a file to S3 with public read access and specified MIME type."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    body_filename = request.form.get('filename', '')

    if file.filename == "":
        return jsonify({"error": "No file selected for uploading"}), 400

    if file:
        filename = secure_filename(file.filename)
        s3_object_name = f"{int(time.time() * 1000)}-{filename}"
        if body_filename:
            s3_object_name = body_filename

        # Determine the MIME type of the file
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            return jsonify({"error": "Could not determine the file's MIME type"}), 400
            # mime_type = "application/octet-stream"  # Default MIME type if not detected

        try:
            s3.upload_fileobj(
                file,
                S3_BUCKET_NAME,
                s3_object_name,
                ExtraArgs={
                    "ACL": "public-read",  # Make the file publicly accessible
                    "ContentType": mime_type  # Specify the MIME type
                }
            )
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "s3_location": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_object_name}"
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

def upload_to_s3(file, custom_filename=None):
    """Helper function to upload a single file to S3."""
    if file.filename == "":
        return {"error": "Empty filename"}, 400

    filename = secure_filename(file.filename)
    timestamp = int(time.time() * 1000)
    s3_object_name = f"{timestamp}-{filename}" if not custom_filename else custom_filename

    # Determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if not detected

    try:
        s3.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            s3_object_name,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": mime_type
            }
        )
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "filename": filename,
            "s3_location": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_object_name}"
        }, 201
    except Exception as e:
        return {"status": "error", "error": str(e), "filename": filename}, 500

def update_to_s3(file, custom_filename=None):
    """Helper function to update (overwrite) a single file in S3."""
    if file.filename == "":
        return {"error": "Empty filename"}, 400

    filename = secure_filename(file.filename)
    s3_object_name = custom_filename if custom_filename else filename

    # Determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if not detected

    try:
        print("MIME TYPE:", mime_type)
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_object_name, Body=file, ContentType=mime_type, ACL='public-read')
        return {
            "status": "success",
            "message": "File updated successfully",
            "filename": filename,
            "s3_location": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_object_name}"
        }, 201
    except Exception as e:
        return {"status": "error", "error": str(e), "filename": filename}, 500

@app.route("/reupload/bulk", methods=["POST"])
def bulk_upload():
    """Endpoint to upload multiple files to S3 with public read access."""
    if "files" not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist("files")
    if not files or all(file.filename == "" for file in files):
        return jsonify({"error": "No files selected for uploading"}), 400

    custom_filenames = request.form.getlist('filenames')  # Optional custom filenames
    results = []
    total_success = 0
    total_failed = 0

    for idx, file in enumerate(files):
        custom_filename = custom_filenames[idx] if idx < len(custom_filenames) else None
        result, status_code = update_to_s3(file, custom_filename)
        results.append(result)
        if status_code == 201:
            total_success += 1
        else:
            total_failed += 1

    # Determine response status code
    if total_failed == 0 and total_success > 0:
        status_code = 201
    elif total_success == 0:
        status_code = 500
    else:
        status_code = 207  # Partial success

    response = {
        "total_files": total_success + total_failed,
        "successful_uploads": total_success,
        "failed_uploads": total_failed,
        "results": results
    }

    return jsonify(response), status_code

# @app.route("/reupload/from-urls", methods=["POST"])
# def bulk_upload_from_urls():
#     """Endpoint to upload multiple files from URLs to S3."""
#     if not request.is_json:
#         return jsonify({"error": "Request must be JSON"}), 400

#     data = request.get_json()
#     if not data or "urls" not in data:
#         return jsonify({"error": "No URLs provided in request"}), 400

#     urls = data["urls"]
#     custom_filenames = data.get("filenames", [])  # Optional custom filenames
#     results = []
#     total_success = 0
#     total_failed = 0

#     for idx, url in enumerate(urls):
#         try:
#             # Download the image from URL
#             response = requests.get(url)
#             response.raise_for_status()
#             # Create file-like object from downloaded content
#             file_obj = BytesIO(response.content)
#             # Extract filename from URL
#             url_filename = url.split('/')[-1]
#             file_obj.filename = url_filename  # Add filename attribute for compatibility
#             # Get custom filename if provided
#             custom_filename = custom_filenames[idx] if idx < len(custom_filenames) else None
#             # Upload to S3
#             result, status_code = update_to_s3(file_obj, custom_filename)
#             results.append(result)

#             if status_code == 201:
#                 total_success += 1
#             else:
#                 total_failed += 1
#         except Exception as e:
#             results.append({
#                 "status": "error",
#                 "error": str(e),
#                 "url": url
#             })
#             total_failed += 1

#     # Determine response status code
#     if total_failed == 0 and total_success > 0:
#         status_code = 201
#     elif total_success == 0:
#         status_code = 500
#     else:
#         status_code = 207

#     response = {
#         "total_urls": total_success + total_failed,
#         "successful_uploads": total_success,
#         "failed_uploads": total_failed,
#         "results": results
#     }

#     return jsonify(response), status_code

CORS(app, resources={
    r"/*": {
        "origins": [
            "https://tsuzumijapan.com",
            "https://dev.tsuzumijapan.com",
            "http://tsuzumijapan.com",
            "http://dev.tsuzumijapan.com"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

if __name__ == "__main__":
    app.run(debug=True)
