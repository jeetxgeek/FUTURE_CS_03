from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from encryption import encrypt_file, decrypt_file

app = Flask(__name__)
app.secret_key = "supersecretkey"  # flash messages ke liye

UPLOAD_FOLDER = "encrypted_files"
DOWNLOAD_FOLDER = "downloads"
KEY_FILE = "key.key"

# Create folders if not exists
for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Generate AES key if not exists
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as keyfile:
        keyfile.write(os.urandom(16))  # 128-bit AES key

# Load AES key
with open(KEY_FILE, "rb") as kf:
    key = kf.read()

# ---------------- Routes ---------------- #

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    data = file.read()

    # Encrypt file
    nonce, tag, encrypted_data = encrypt_file(key, data)

    # Save encrypted file
    filepath = os.path.join(UPLOAD_FOLDER, file.filename + ".enc")
    with open(filepath, "wb") as f:
        f.write(nonce + tag + encrypted_data)

    flash(f"✅ File '{file.filename}' encrypted & uploaded successfully!")
    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        flash(f"❌ File '{filename}' not found!")
        return redirect(url_for("index"))

    with open(filepath, "rb") as f:
        content = f.read()

    nonce = content[:16]
    tag = content[16:32]
    ciphertext = content[32:]

    # Decrypt file
    decrypted = decrypt_file(key, nonce, tag, ciphertext)

    # Save decrypted file to downloads folder
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    outname = os.path.join(DOWNLOAD_FOLDER, filename.replace(".enc", ""))
    with open(outname, "wb") as f:
        f.write(decrypted)

    flash(f"✅ File '{filename}' decrypted & downloaded successfully!")
    return send_file(outname, as_attachment=True)

@app.route("/files")
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("files_list.html", files=files)

# ---------------------------------------------- #

if __name__ == "__main__":
    app.run(debug=True)
