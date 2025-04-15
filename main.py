import http.client
import os
import urllib.parse
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify

# 設定 API 主機
HOST = "graph.threads.net"

app = Flask(__name__)

def get_user_info(access_token):
    endpoint = "/v1.0/me"
    params = {
        "access_token": access_token,
        "fields": "id,name",
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"

    conn = http.client.HTTPSConnection(HOST)
    conn.request("GET", url)

    response = conn.getresponse()
    body = response.read().decode()
    conn.close()

    print("User Info:", body)
    return body

def create_thread(access_token, text):
    endpoint = "/v1.0/me/threads"
    params = {
        "access_token": access_token,
        "media_type": "TEXT",
        "text": text,
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"

    conn = http.client.HTTPSConnection(HOST)
    conn.request("POST", url)

    response = conn.getresponse()
    body = response.read().decode()
    conn.close()

    print("Thread Creation Response:", body)
    data = json.loads(body)
    return data.get("id") if data else None

def publish_thread(access_token, creation_id):
    endpoint = "/v1.0/me/threads_publish"
    params = {
        "access_token": access_token,
        "creation_id": creation_id,
    }
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"

    conn = http.client.HTTPSConnection(HOST)
    conn.request("POST", url)

    response = conn.getresponse()
    body = response.read().decode()
    conn.close()

    print("Publish Response:", body)
    return body

def save_note_version(note):
    """
    保存筆記版本，最多保留 10 個版本
    """
    file_path = "notes_versions.txt"
    notes = []

    # 如果檔案存在，讀取現有版本
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            notes = file.readlines()

    # 新增最新版本到列表
    notes.insert(0, note + "\n")

    # 保留最多 10 個版本
    notes = notes[:10]

    # 將版本寫回檔案
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(notes)

def load_note_versions():
    """
    讀取筆記版本
    """
    file_path = "notes_versions.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readlines()
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("note")
        if text:
            # 保存筆記版本
            save_note_version(text)
        return "Note saved!"

    # 讀取已保存的筆記版本
    notes = load_note_versions()
    return render_template("index.html", notes=notes)
@app.route("/notes", methods=["GET"])
def get_notes():
    """
    返回最新的筆記版本（最多 10 個）
    """
    notes = load_note_versions()
    return jsonify({"notes": notes})

@app.route("/publish", methods=["POST"])
def publish():
    text = request.form.get("note")
    if text:
        # 保存筆記版本
        save_note_version(text)

        access_token = os.getenv("THREADS_API_ACCESS_TOKEN")
        if not access_token:
            return "請設定環境變數 THREADS_API_ACCESS_TOKEN", 400

        creation_response = create_thread(access_token, text)
        creation_id = creation_response

        publish_response = publish_thread(access_token, creation_id)
        return "Note published to Threads!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)