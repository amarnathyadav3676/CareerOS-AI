import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory
from db.database import init_db
from routes.auth import auth_bp
from routes.progress import prog_bp

app = Flask(__name__, static_folder="public")

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return r

@app.before_request
def opts():
    from flask import request
    if request.method == "OPTIONS":
        return jsonify({}), 200

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(prog_bp, url_prefix="/api/progress")

@app.route("/api/health")
def health():
    return jsonify({"status":"ok","app":"CareerOS","version":"2.0"})

@app.route("/")
@app.route("/login")
@app.route("/register")
@app.route("/dashboard")
def index():
    return send_from_directory("public", "index.html")

@app.errorhandler(404)
def not_found(e): return jsonify({"error":"Not found"}), 404

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 CareerOS server: http://localhost:{port}")
    print(f"📖 API health:     http://localhost:{port}/api/health")
    app.run(debug=True, port=port, host="0.0.0.0")