import os
import argparse
import io
import zipfile
import shutil
from datetime import datetime, timezone

from flask import Flask, send_from_directory, render_template, jsonify, request, Response, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin

import util

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=str, default=5000,
                    help='Base directory to navigate from')
args = parser.parse_args()

app = Flask(__name__)
app.config['SECRET_KEY'] = util.get_secret_key()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filebuddy.db'
app.config['USER_FILES_DIR'] = 'user_dirs'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    directory = db.Column(db.String(300), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)


@app.route("/", methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('filebuddy'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('filebuddy'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template("home.html")


@app.route("/filebuddy")
@login_required
def filebuddy():
    return render_template("filebuddy.html", username=current_user.username)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_directory = os.path.join(app.config['USER_FILES_DIR'], username)

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
        else:
            os.makedirs(user_directory, exist_ok=True)
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=hashed_password,
                directory=user_directory
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('home'))

    return render_template('register.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route("/files", methods=["GET"])
def get_directory_tree():
    """Get the directory tree"""
    path = request.args.get('path', '')
    if not util.is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    full_path = os.path.join(base_dir, path) if path else base_dir

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
                    "path": os.path.relpath(full_entry_path, base_dir).replace('\\', '/')
                }
                if os.path.isdir(full_entry_path):
                    entry['type'] = "directory"
                tree.append(entry)
        except FileNotFoundError:
            return []  # Handle case where the directory doesn't exist anymore
        return tree
    
    return jsonify(get_tree(full_path))


@app.route('/delete', methods=['POST'])
@login_required
def delete():
    data = request.get_json()
    directory = data.get('directory')
    filename = data.get('filename')
    rel_path = os.path.join(directory, filename)
    if not util.is_valid_path(rel_path):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    full_path = os.path.join(base_dir, rel_path)

    if os.path.exists(full_path):
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                util.rmdir(full_path)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'File or folder not found'}), 404


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Download a specific file"""
    directory = request.args.get('directory', '')
    if not util.is_valid_path(directory):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    dir_path = os.path.join( base_dir, directory) if directory else base_dir
    return send_from_directory(dir_path, filename, as_attachment=True)


@app.route("/download-directory", methods=["GET"])
def download_directory_stream():
    """Stream the entire directory as a .zip file."""
    path = request.args.get("path", "")
    if not util.is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    full_path = os.path.join(base_dir, path)

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
    if not util.is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    full_path = os.path.join(base_dir, path)

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


@app.route("/upload", methods=["POST"])
def upload_files():
    """Handle file uploads."""
    path = request.form.get("path", "")
    if not util.is_valid_path(path):
        return jsonify({"error": "Invalid path"}), 400

    base_dir = current_user.directory
    full_path = os.path.join(base_dir, path)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({"error": "Invalid path"}), 400

    files = request.files.getlist("files")
    for file in files:
        file_path = os.path.join(full_path, file.filename)
        file.save(file_path)

    return jsonify({"success": True, "message": "Files uploaded successfully."})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    os.makedirs(app.config['USER_FILES_DIR'], exist_ok=True)
    app.run(host='0.0.0.0', port=args.port, debug=True)
