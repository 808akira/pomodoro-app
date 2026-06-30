from flask import Flask, render_template, request, jsonify
import os, time
import pyodbc
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

def get_conn():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['SQL_SERVER']};"
        f"DATABASE={os.environ['SQL_DATABASE']};"
        f"UID={os.environ['SQL_USERNAME']};"
        f"PWD={os.environ['SQL_PASSWORD']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def init_db():
    with get_conn() as conn:
        conn.execute("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects WHERE name='scores' AND xtype='U'
            )
            CREATE TABLE scores (
                id       INT IDENTITY PRIMARY KEY,
                name     NVARCHAR(20)  NOT NULL,
                score    INT           NOT NULL,
                ts       BIGINT        NOT NULL
            )
        """)
        conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test-vnet")
def test_vnet():
    try:
        r = requests.get("http://web-app-samy-private.azurewebsites.net/ping", timeout=5)
        return jsonify({"depuis": "App A (publique)", "reponse_app_b": r.json()})
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/api/scores", methods=["GET"])
def get_scores():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT TOP 10 name, score FROM scores ORDER BY score DESC"
        ).fetchall()
    return jsonify([{"name": r[0], "score": r[1]} for r in rows])

@app.route("/api/scores", methods=["POST"])
def post_score():
    data = request.get_json()
    name  = (data.get("name") or "Anonyme")[:20].strip() or "Anonyme"
    score = int(data.get("score", 0))
    if score <= 0:
        return jsonify({"error": "score invalide"}), 400

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO scores (name, score, ts) VALUES (?, ?, ?)",
            (name, score, int(time.time()))
        )
        conn.commit()
        rank  = conn.execute(
            "SELECT COUNT(*) FROM scores WHERE score >= ?", (score,)
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]

    return jsonify({"rank": rank, "total": total})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

with app.app_context():
    try:
        init_db()
    except Exception:
        pass
