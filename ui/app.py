from flask import Flask, render_template, request, redirect, url_for
import json
import http.client
import urllib.parse

app = Flask(__name__)

# 設定 API 主機
HOST = "graph.threads.net"
access_token = "THACDQ1Ea7ww5BYlVmZA3dObTVLWk0zMFZAjTFcwdkNKZAmREZAkhyWmNCRGhtYTFRakw2OGU3Y1FlbnRSbl95WjlBbm9lVXFxSlNDYk1EX2lIM0V2b01qaUEtRW55Mm05T1pWZAGJZAemY1RGRDYjVNNzg1NDg4OFZAKbGJhcTJpa0p6ZAzJJQXJRRlZAmX1pRcmU5cXA3NzBCQ01IdTdwZAwZDZD"

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

    data = json.loads(body)
    return data.get("id") if data else None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        note = request.form['note']
        if note:
            creation_id = create_thread(access_token, note)
            if creation_id:
                return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)