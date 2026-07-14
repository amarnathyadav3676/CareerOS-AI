import os
import time
import jwt

from functools import wraps
from flask import request, jsonify, g

from db.database import get_db

SECRET = os.environ.get("JWT_SECRET", "careeros-secret-amar-2029")


def make_token(user_id):
    payload = {
        "uid": user_id,
        "exp": int(time.time()) + (60 * 60 * 24 * 30)  # 30 days
    }

    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        auth = request.headers.get("Authorization", "")

        if not auth.startswith("Bearer "):
            return jsonify({"error": "Login required"}), 401

        token = auth.replace("Bearer ", "").strip()

        payload = decode_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE id=?",
            (payload["uid"],)
        ).fetchone()

        db.close()

        if not user:
            return jsonify({"error": "User not found"}), 401

        g.user = dict(user)

        return func(*args, **kwargs)

    return wrapper