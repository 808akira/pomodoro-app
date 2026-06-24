from flask import Flask, render_template, request, jsonify, session
import json, os, time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

SCORES_FILE = "scores.json"

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            return json.load(f)
    return []

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scores", methods=["GET"])
def get_scores():
    scores = load_scores()
    top10 = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return jsonify(top10)

@app.route("/api/scores", methods=["POST"])
def post_score():
    data = request.get_json()
    name = (data.get("name") or "Anonyme")[:20].strip() or "Anonyme"
    score = int(data.get("score", 0))
    if score <= 0:
        return jsonify({"error": "score invalide"}), 400

    scores = load_scores()
    scores.append({"name": name, "score": score, "ts": int(time.time())})
    # Garder seulement les 100 derniers pour ne pas gonfler le fichier
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:100]
    save_scores(scores)
    rank = next((i + 1 for i, s in enumerate(scores) if s["score"] == score and s["name"] == name), None)
    return jsonify({"rank": rank, "total": len(scores)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
