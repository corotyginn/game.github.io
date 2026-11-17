import sqlite3
import os
import re
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pixels.db")
GRID_W = 64
GRID_H = 64
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pixels (
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            color TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (x, y)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html", W=GRID_W, H=GRID_H)


@app.route("/api/pixels")
def api_pixels():
    conn = get_db()
    rows = conn.execute("SELECT x, y, color FROM pixels").fetchall()
    conn.close()
    return jsonify([{"x": r["x"], "y": r["y"], "c": r["color"]} for r in rows])


@app.route("/api/pixel", methods=["POST"])
def api_set_pixel():
    data = request.get_json(silent=True) or {}
    try:
        x = int(data.get("x"))
        y = int(data.get("y"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "bad coords"}), 400
    color = data.get("c", "")
    if not (0 <= x < GRID_W and 0 <= y < GRID_H):
        return jsonify({"ok": False, "error": "out of bounds"}), 400
    if not isinstance(color, str) or not HEX_RE.match(color):
        return jsonify({"ok": False, "error": "bad color"}), 400
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO pixels (x, y, color) VALUES (?, ?, ?)",
        (x, y, color.lower()),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
