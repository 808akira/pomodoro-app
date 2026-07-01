from flask import Flask, render_template, jsonify
import os, requests

app = Flask(__name__)

BACKEND_URL = "http://web-app-samy-private.azurewebsites.net"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/backend-status")
def backend_status():
    try:
        r = requests.get(f"{BACKEND_URL}/status", timeout=5)
        return jsonify({"reachable": True, "data": r.json()})
    except Exception as e:
        return jsonify({"reachable": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
