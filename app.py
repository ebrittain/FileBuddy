import os
from flask import Flask, send_from_directory, jsonify, request, Response
import argparse
import io
import zipfile

app = Flask(__name__, static_folder='static')

parser = argparse.ArgumentParser()
parser.add_argument('--base-dir', type=str, required=True,
                    help='Base directory to navigate from')
args = parser.parse_args()


PASSWORD = "12345"  # Replace with your desired password


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/files", methods=["GET"])
def get_directory_tree():
    """Get the directory tree"""
    path = request.args.get('path', '')
    full_path = os.path.join(args.base_dir, path) if path else args.base_dir

    def get_tree(path):
        tree = []
        try:
            for entry in os.listdir(path):
                if entry.startswith('.'):
                    continue
                full_entry_path = os.path.join(path, entry)
                entry = {
                    "name": entry,
                    "type": "file",
                    "path": os.path.relpath(full_entry_path, args.base_dir).replace('\\', '/')
                }
                if os.path.isdir(full_entry_path):
                    entry['type'] = "directory"
                tree.append(entry)
        except FileNotFoundError:
            return []  # Handle case where the directory doesn't exist anymore
        return tree
    
    return jsonify(get_tree(full_path))


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Download a specific file"""
    directory = request.args.get('directory', '')
    dir_path = os.path.join(args.base_dir, directory) if directory else args.base_dir
    return send_from_directory(dir_path, filename, as_attachment=True)


@app.route("/download-directory", methods=["GET"])
def download_directory_stream():
    """Stream the entire directory as a .zip file."""
    path = request.args.get("path", "")
    full_path = os.path.join(args.base_dir, path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({"error": "Directory does not exist"}), 404

    def generate_zip():
        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, full_path)
                        zipf.write(file_path, arcname)
            zip_buffer.seek(0)
            yield zip_buffer.read()

    return Response(generate_zip(), mimetype="application/zip", headers={
        "Content-Disposition": f"attachment; filename={os.path.basename(full_path)}.zip"
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
