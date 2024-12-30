import os
from flask import Flask, send_from_directory, jsonify, request, Response
import argparse
import io
import zipfile

app = Flask(__name__, static_folder='static')

parser = argparse.ArgumentParser()
parser.add_argument('--base-dir', type=str, required=True,
                    help='Base directory to navigate from')
parser.add_argument('--port', type=str, default=5000,
                    help='Base directory to navigate from')
args = parser.parse_args()


def is_valid_path(path):
    """Validate that the path does not contain invalid sequences like '..'."""
    return ".." not in path and not os.path.isabs(path)


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/files", methods=["GET"])
def get_directory_tree():
    """Get the directory tree"""
    path = request.args.get('path', '')
    if not is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

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
    if not is_valid_path(directory):
        return jsonify({"error": "Invalid path"}), 400

    dir_path = os.path.join(args.base_dir, directory) if directory else args.base_dir
    return send_from_directory(dir_path, filename, as_attachment=True)


@app.route("/download-directory", methods=["GET"])
def download_directory_stream():
    """Stream the entire directory as a .zip file."""
    path = request.args.get("path", "")
    if not is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

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


@app.route("/search", methods=["GET"])
def search_files():
    """Recursively search for files and directories matching the query."""
    query = request.args.get("query", "").lower()
    path = request.args.get("path", "")
    if not is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

    full_path = os.path.join(args.base_dir, path)

    if not os.path.exists(full_path):
        return jsonify({"error": "Path does not exist"}), 404

    results = []
    for root, dirs, files in os.walk(full_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for name in dirs + files:
            if name.startswith('.'):
                continue
            if query in name.lower():
                relative_root = os.path.relpath(root, full_path).replace("\\", "/")
                relative_path = f"{relative_root}/{name}" if relative_root != "." else name
                item_type = "directory" if os.path.isdir(os.path.join(root, name)) else "file"
                results.append({
                    "name": name,
                    "type": item_type,
                    "relative_path": relative_path
                })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=args.port, debug=True)
