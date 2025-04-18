import http.client
import os
import urllib.parse
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
# 載入 .env 檔案
from dotenv import load_dotenv 
load_dotenv()
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
            notes = file.read().strip().split("\n\n")

    # 新增最新版本到列表
    notes.insert(0, note)

    # 保留最多 10 個版本
    notes = notes[:10]

    # 將版本寫回檔案，使用雙換行符號分隔
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n\n".join(notes))

def load_note_versions():
    """
    讀取筆記版本
    """
    file_path = "notes_versions.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            notes = file.read().strip().split("\n\n")  # 使用雙換行符號分隔筆記
            return notes
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

def split_note(note, max_length=500):
    """
    將筆記拆分為多段，每段不超過 max_length 字元，並在每段前加上第一行作為日期標籤
    """
    lines = note.split("\n")
    first_line = lines[0]+"\n"+lines[1]  # 取得第一行作為日期標籤
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:  # +1 是為了考慮換行符號
            chunks.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += line + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # 在每段前加上第一行（日期標籤），除了第一段
    return [chunks[0]] + [f"{first_line}\n{chunk}" for chunk in chunks[1:]]


@app.route("/publish", methods=["POST"])
def publish():
    text = request.form.get("note")
    user = request.form.get("user")  # 接收選擇的使用者
    if text:
        # 根據選擇的使用者取得對應的 access token
        if user == "user1":
            access_token = os.getenv("THREADS_API_ACCESS_TOKEN_USER1")
        elif user == "user2":
            access_token = os.getenv("THREADS_API_ACCESS_TOKEN_USER2")
        else:
            return jsonify({"error": "無效的使用者選擇"}), 401

        if not access_token:
            return jsonify({"error": "請設定環境變數 THREADS_API_ACCESS_TOKEN"}), 402

        # 拆分筆記（如果超過 500 字）
        chunks = split_note(text)

        # 保存每段筆記並發佈
        for chunk in chunks:
            # 保存筆記版本
            save_note_version(chunk)

            # 創建 Thread
            creation_response = create_thread(access_token, chunk)
            creation_id = creation_response

            # 發佈 Thread
            publish_response = publish_thread(access_token, creation_id)

        return jsonify({"message": "Note published to Threads!", "chunks": chunks})

    return jsonify({"error": "請提供筆記內容"}), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)