import http.client
import os
import urllib.parse
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
# 載入 .env 檔案
from dotenv import load_dotenv 
load_dotenv()
# 設定 API 主機
HOST = "graph.threads.net"

app = Flask(__name__)

@app.route("/ai-complete", methods=["POST"])
def ai_complete():
    """
    使用 AI 服務生成文本補全
    """
    try:
        data = request.get_json()
        text = data.get("text", "")
        
        if not text or len(text) < 2:
            return jsonify({"error": "文本太短"}), 400
        
        # 使用 OpenAI API 或其他 AI 服務來獲取補全
        # 這裡以 OpenAI API 為例
        completion = get_ai_completion(text)
        print(f"返回補全: {completion[:30] if completion else 'None'}...")
        return jsonify({"completion": completion})
    
    except Exception as e:
        print(f"AI 補全錯誤: {e}")
        return jsonify({"error": str(e)}), 500

def get_ai_completion(text):
    """
    調用 OpenAI API 獲取文本補全
    """
    try:
        # 獲取 API 密鑰
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            print("使用模擬補全，因為沒有找到 API 密鑰")
            # 模擬英文單字補全
            if text.lower().startswith("a"):
                return text + "bandon [v.] 放棄，遺棄；離開"
            elif text.lower().startswith("c"):
                return text + "omprehend [v.] 理解，領會；包含"
            elif text.lower().startswith("e"):
                return text + "fficient [adj.] 高效的，有能力的；[n.] 效率"
            else:
                return text + " - [n.] 名詞；[v.] 動詞；[adj.] 形容詞"
            
        # 調用 OpenAI API，使用 GPT-4o-mini
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-4o-mini",  # 使用 GPT-4o-mini 模型
            "messages": [
                {
                    "role": "system", 
                    "content": """你是一個專業的英語單字助手，專門提供英文單字的中文翻譯與用法。
                    
                    當用戶輸入英文單字或字首時，請按照以下格式提供補全：
                    1. 補全單字完整形式
                    2. 標註詞性，使用 [n.], [v.], [adj.], [adv.] 等標準縮寫
                    3. 列出2-4個常用中文翻譯，以逗號分隔
                    4. 對於有多種詞性的單字，用分號分隔不同詞性的解釋
                    
                    例如：
                    用戶輸入："ab"
                    你的回應："abandon [v.] 放棄，遺棄，拋下，離開；[n.] 放縱，縱情"
                    
                    用戶輸入："ef"
                    你的回應："efficient [adj.] 高效的，有能力的，能勝任的；[n.] 效率"
                    
                    請務必：
                    - 直接補全用戶輸入，不要重複已輸入的部分
                    - 不要包含任何解釋或其他文字
                    - 翻譯要簡潔、準確、全面
                    - 側重常用詞義和常見搭配
                    - 只提供一個最相關的單字補全
                    
                    - 如果某個詞性的意思與其他詞性相似，可以不重複列出"""
                },
                {
                    "role": "user", 
                    "content": f"以下是我的英文筆記，請幫我補全並翻譯英文單字，且避免補全，例如已經有apple蘋果，就不要再出現apple蘋果：{text}"
                }
            ],
            "temperature": 0.2,  # 降低溫度值以獲取更確定的回答
            "max_tokens": 100
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            completion = result["choices"][0]["message"]["content"].strip()
            
            # 直接將補全添加到原始文本後
            return text + completion
        else:
            print(f"API 錯誤: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        print(f"獲取 AI 補全錯誤: {e}")
        return None
    
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
@app.route("/ask", methods=["POST"])
def ask_question():
    """
    處理 AI 問答請求
    """
    try:
        data = request.get_json()
        question = data.get("question", "")
        
        if not question:
            return jsonify({"error": "問題不能為空"}), 400
        
        # 使用 OpenAI API 獲取回答
        answer = get_ai_answer(question)
        
        return jsonify({"answer": answer})
    
    except Exception as e:
        print(f"AI 問答錯誤: {e}")
        return jsonify({"error": str(e)}), 500

def get_ai_answer(question):
    """
    使用 OpenAI API 獲取問題的回答
    """
    try:
        # 獲取 API 密鑰
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            print("使用模擬回答，因為沒有找到 API 密鑰")
            # 提供一些模擬回答用於測試
            if "天氣" in question:
                return "我無法獲取即時天氣信息，但您可以通過天氣應用或網站查詢當地天氣。"
            elif "時間" in question:
                from datetime import datetime
                now = datetime.now()
                return f"現在的時間是 {now.strftime('%H:%M:%S')}。"
            elif "名字" in question:
                return "我是您的 AI 助手，很高興能幫助您！"
            else:
                return "很抱歉，由於環境限制，無法提供完整回答。請確保已設置有效的 API 密鑰。"
        
        # 使用 OpenAI API 獲取回答
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一個有幫助的助手，提供簡明、準確的回答。"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            return answer
        else:
            print(f"API 錯誤: {response.status_code}, {response.text}")
            return "很抱歉，無法處理您的請求。請稍後再試。"
            
    except Exception as e:
        print(f"獲取 AI 回答錯誤: {e}")
        return "出現錯誤，無法獲取回答。"
    
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