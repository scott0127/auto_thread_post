import http.client
import os
import urllib.parse
import json
import requests
import tempfile
import re
from flask import Flask, render_template, request, redirect, url_for, jsonify
# 載入 .env 檔案
from dotenv import load_dotenv 
load_dotenv()
# 設定 API 主機
HOST = "graph.threads.net"

app = Flask(__name__)


def split_srt_content(srt_content, max_lines=40):
    """
    將 SRT 內容依區塊分段，每段不超過 max_lines 區塊
    """
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    chunks = []
    current = []
    for block in blocks:
        current.append(block)
        if len(current) >= max_lines:
            chunks.append('\n\n'.join(current))
            current = []
    if current:
        chunks.append('\n\n'.join(current))
    return chunks

@app.route("/generate-subtitle", methods=["POST"])
def generate_subtitle():
    """
    上傳字幕檔（.srt/.vtt），轉為繁體中文後下載（自動分段避免中斷）
    """
    try:
        if "subtitle" not in request.files:
            return jsonify({"error": "請上傳字幕檔案"}), 400
        subtitle_file = request.files["subtitle"]

        # 將字幕暫存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp:
            subtitle_path = tmp.name
            subtitle_file.save(subtitle_path)

        # 讀取字幕內容
        with open(subtitle_path, "r", encoding="utf-8") as f:
            subtitle_content = f.read()

        # 分段處理
        chunks = split_srt_content(subtitle_content, max_lines=40)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "未設定 OPENAI_API_KEY"}), 401

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        translated_chunks = []
        for idx, chunk in enumerate(chunks):
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一個字幕翻譯助手，請將收到的字幕內容翻譯成繁體中文，保留字幕格式（如 SRT/VTT 標號與時間碼），只翻譯字幕內容。"
                    },
                    {
                        "role": "user",
                        "content": chunk
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=600
            )
            if response.status_code == 200:
                translated = response.json()["choices"][0]["message"]["content"]
                translated_chunks.append(translated)
            else:
                os.remove(subtitle_path)
                return jsonify({"error": f"第{idx+1}段翻譯失敗: {response.text}"}), 500

        os.remove(subtitle_path)
        translated_subtitle = "\n\n".join(translated_chunks)
        # 回傳檔案下載
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8") as out_tmp:
            out_tmp.write(translated_subtitle)
            out_path = out_tmp.name
        from flask import send_file
        return send_file(out_path, as_attachment=True, download_name="subtitle_zh-TW.srt", mimetype="text/plain")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """
    上傳字幕檔（.srt/.vtt），轉為繁體中文後下載
    """
    try:
        if "subtitle" not in request.files:
            return jsonify({"error": "請上傳字幕檔案"}), 400
        subtitle_file = request.files["subtitle"]

        # 將字幕暫存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp:
            subtitle_path = tmp.name
            subtitle_file.save(subtitle_path)

        # 讀取字幕內容
        with open(subtitle_path, "r", encoding="utf-8") as f:
            subtitle_content = f.read()

        # 呼叫 OpenAI API 進行翻譯
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "未設定 OPENAI_API_KEY"}), 401

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一個字幕翻譯助手，請將收到的字幕內容翻譯成繁體中文，保留字幕格式（如 SRT/VTT 標號與時間碼），只翻譯字幕內容。"
                },
                {
                    "role": "user",
                    "content": subtitle_content
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=600
        )
        os.remove(subtitle_path)
        if response.status_code == 200:
            translated_subtitle = response.json()["choices"][0]["message"]["content"]
            # 回傳檔案下載
            with tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8") as out_tmp:
                out_tmp.write(translated_subtitle)
                out_path = out_tmp.name
            from flask import send_file
            return send_file(out_path, as_attachment=True, download_name="subtitle_zh-TW.srt", mimetype="text/plain")
        else:
            return jsonify({"error": response.text}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
@app.route("/generate-image", methods=["POST"])
def generate_image():
    """
    使用 OpenAI DALL-E 3 生成圖像，並強化風格控制
    """
    try:
        data = request.get_json()
        base_prompt = data.get("prompt", "")
        style = data.get("style", "")  # 接收風格參數
        
        if not base_prompt:
            return jsonify({"error": "請提供圖像描述"}), 400

        # 風格庫 - 包含預定義的風格和詳細描述
        style_guides = {
            "吉卜力": "宮崎駿吉卜力工作室風格，溫暖柔和的色調，細膩的自然場景，富有童話感但具有深度的人物設計",
            "水墨畫": "傳統東方水墨畫風格，濃淡層次分明，水墨暈染效果，留白的藝術表現，意境深遠",
            "浮世繪": "日本浮世繪風格，平面構圖，大膽的色彩對比，細膩的線條，如北齋、歌川廣重的作品",
            "賽博龐克": "賽博龐克風格，未來都市霓虹燈光，高科技低生活的對比，強烈的色彩對比，陰暗潮濕的街道",
            "蒸汽龐克": "蒸汽龐克風格，維多利亞時代的機械裝置，黃銅和銅色調，蒸汽動力機械，齒輪和管道",
            "超現實主義": "超現實主義風格，如達利的作品，夢境般的場景，不合邏輯的元素組合，精細的寫實技法",
            "立體主義": "立體主義風格，如畢卡索的作品，同時呈現多個視角，幾何形狀分解，平面而抽象",
            "新藝術": "新藝術風格，曲線優美的裝飾線條，自然界的有機形態，精緻的細節和華麗的裝飾元素",
            "低多邊形": "低多邊形3D渲染風格，幾何面構成，色彩分明，簡化的形態，現代數位藝術感",
            "像素藝術": "復古像素藝術風格，明確可見的像素點，有限調色板，精確的直角邊緣，8位或16位遊戲美學",
            "科幻插畫": "科幻插畫風格，未來星系和行星場景，高科技宇宙飛船，壯觀的太空景觀，細節豐富的技術表現",
            "哥特": "哥特風格，黑暗神秘氛圍，尖塔和拱門，華麗複雜的裝飾，強烈光影對比，中世紀建築元素",
            "赤道摩洛哥風": "明亮熱情的摩洛哥風格，複雜的幾何圖案，鮮豔的色彩對比，精緻的馬賽克紋理，異國情調的建築元素"
        }
        
        # 構建增強的提示詞
        enhanced_prompt = base_prompt
        
        # 處理風格
        if style:
            # 檢查是否為預定義風格
            style_guide = style_guides.get(style)
            
            if style_guide:
                # 使用預定義風格描述
                enhanced_prompt = f"以下圖像必須完全遵循{style}風格：{style_guide}。圖像內容是：{base_prompt}"
            else:
                # 使用用戶自定義風格
                enhanced_prompt = f"以下圖像必須完全遵循{style}風格，強烈體現該風格的所有特徵和視覺元素。圖像內容是：{base_prompt}"
        
        # 添加通用品質提升詞
        enhanced_prompt += "。圖像品質要求：高度細節，完美構圖，藝術品質，專業攝影技術，極致精細的紋理細節"
            
        print(f"使用增強提示詞: {enhanced_prompt}")
            
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "未設定 OPENAI_API_KEY"}), 401

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "model": "dall-e-3",
            "prompt": enhanced_prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "hd"  # 使用高品質設置
        }
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            image_url = result["data"][0]["url"]
            return jsonify({
                "image_url": image_url,
                "prompt_used": enhanced_prompt  # 返回實際使用的提示詞
            })
        else:
            return jsonify({"error": response.text}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """
    使用 OpenAI gpt-image-1 (DALL·E 3) 生成圖像
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        if not prompt:
            return jsonify({"error": "請提供圖像描述"}), 400

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "未設定 OPENAI_API_KEY"}), 401

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            image_url = response.json()["data"][0]["url"]
            return jsonify({"image_url": image_url})
        else:
            return jsonify({"error": response.text}), 500
    except Exception as e:
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
            # 模擬英文單字補全 - 只返回補全部分而不包含原始文本
            if text.lower().startswith("a"):
                return "bandon [v.] 放棄，遺棄；離開"
            elif text.lower().startswith("c"):
                return "omprehend [v.] 理解，領會；包含"
            elif text.lower().startswith("e"):
                return "fficient [adj.] 高效的，有能力的；[n.] 效率"
            else:
                return " [n.] 測試，考試，檢驗；[v.] 測試，考驗，檢查"
            
        # 調用 OpenAI API，使用 GPT-4o-mini
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": """你是一個專業的英語單字、片語與句子翻譯助手，專門提供英文輸入的中文翻譯、詞性標註與自然語感補全。

當用戶輸入英文單字、片語或完整句子時，請按照以下格式提供：

1. 以用戶的完整輸入為單位，不拆分單字，不自行切分片語。
2. 同一個單位請保持在同一行輸出，格式如下：
   - 單字或片語原樣顯示（若需補全，請補全後顯示）。
   - 接著詞性標註 [n.]、[v.]、[adj.]、[adv.]、[phr.]。
   - 之後直接列出中文翻譯，每個翻譯用「，」分隔。
   - 如果有多個詞性，用「；」分隔不同詞性的內容。
3. 翻譯2-4個，保持自然、貼近中文常用說法。
4. 若該單字或片語存在多個常見詞性，請**全部列出**，即使其中一個較少見也不可省略。
5. 請遵循詞性優先順序排列：n. > v. > adj. > adv. > phr.。
6. 若用戶輸入的單字或片語未完整，請**優先合理補全至最常見、最符合語境的英文單字或短語**後再進行翻譯。
7. 嚴禁直接翻譯不完整或無明確意義的輸入；應補全後再翻譯。
8. 完整句子一律標記為 [phr.]。

範例：

輸入："where is"  
回應：where is [phr.] 在哪裡，位於哪裡，何處

輸入："abandon"  
回應：abandon [n.] 放縱，縱情；[v.] 放棄，遺棄，拋下，捨棄

輸入："bou"  
回應：bound [adj.] 必然的，受束縛的，準備前往的；[n.] 邊界，界限，限制

請務必遵守以上規則，保持簡潔清楚，方便直接用於筆記。

開始執行。

"""
        },
        {
            "role": "user",
            "content": f"請根據以下英文內容進行補全並翻譯，並以單行格式輸出：\n\n{text}"
        }
    ]
}

        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            completion = result["choices"][0]["message"]["content"].strip()
            
            # 檢查是否包含原始文本，如果包含則移除
            if completion.startswith(text):
                completion = completion[len(text):].strip()
            
            return completion
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
    if len(lines) == 0:
        return []  # 如果筆記為空，直接返回空列表
    elif len(lines) == 1:
        first_line = lines[0]  # 如果只有一行，直接取第一行
    else:
        first_line = lines[0] + "\n" + lines[1]  # 取前兩行作為日期標籤

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