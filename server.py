import os
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import argparse

app = Flask(__name__)
CORS(app)

parser = argparse.ArgumentParser()
parser.add_argument('--base-dir', type=str, required=True,
                    help='Base directory to navigate from')
args = parser.parse_args()

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
                if os.path.isdir(full_entry_path):
                    tree.append({
                        "name": entry,
                        "type": "directory",
                        "path": os.path.relpath(full_entry_path, args.base_dir)
                    })
                else:
                    tree.append({
                        "name": entry,
                        "type": "file",
                        "path": os.path.relpath(full_entry_path, args.base_dir)
                    })
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

if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)
