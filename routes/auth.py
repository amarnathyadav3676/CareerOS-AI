from flask import Blueprint, request, jsonify, g

from db.database import get_db, hash_pw
from middleware.auth import make_token, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    college = data.get("college", "LPU")
    branch = data.get("branch", "CSE")
    year = data.get("year", 2)

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must contain at least 6 characters"}), 400

    db = get_db()

    exists = db.execute(
        "SELECT id FROM users WHERE email=?",
        (email,)
    ).fetchone()

    if exists:
        db.close()
        return jsonify({"error": "Email already registered"}), 409

    cur = db.execute(
        """
        INSERT INTO users
        (name,email,password,college,branch,year)
        VALUES (?,?,?,?,?,?)
        """,
        (
            name,
            email,
            hash_pw(password),
            college,
            branch,
            year
        )
    )

    db.commit()

    uid = cur.lastrowid

    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    ).fetchone()

    db.close()

    user = dict(user)
    user.pop("password", None)

    return jsonify({
        "token": make_token(uid),
        "user": user
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    ).fetchone()

    db.close()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if user["password"] != hash_pw(password):
        return jsonify({"error": "Invalid email or password"}), 401

    user = dict(user)
    user.pop("password", None)

    return jsonify({
        "token": make_token(user["id"]),
        "user": user
    })


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():

    user = dict(g.user)
    user.pop("password", None)

    return jsonify(user)


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():

    data = request.get_json()

    fields = [
        "name",
        "college",
        "branch",
        "year",
        "cgpa",
        "target_role",
        "target_salary",
        "avatar"
    ]

    updates = {
        k: data[k]
        for k in fields
        if k in data
    }

    if not updates:
        return jsonify({"error": "Nothing to update"}), 400

    db = get_db()

    query = ", ".join(f"{k}=?" for k in updates)

    db.execute(
        f"UPDATE users SET {query} WHERE id=?",
        list(updates.values()) + [g.user["id"]]
    )

    db.commit()

    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (g.user["id"],)
    ).fetchone()

    db.close()

    user = dict(user)
    user.pop("password", None)

    return jsonify({
        "message": "Profile updated",
        "user": user
    })


@auth_bp.route("/change-password", methods=["PUT"])
@login_required
def change_password():

    data = request.get_json()

    old = data.get("old_password", "")
    new = data.get("new_password", "")

    if len(new) < 6:
        return jsonify({"error": "Password must contain at least 6 characters"}), 400

    db = get_db()

    row = db.execute(
        "SELECT password FROM users WHERE id=?",
        (g.user["id"],)
    ).fetchone()

    if row["password"] != hash_pw(old):
        db.close()
        return jsonify({"error": "Old password incorrect"}), 400

    db.execute(
        "UPDATE users SET password=? WHERE id=?",
        (
            hash_pw(new),
            g.user["id"]
        )
    )

    db.commit()
    db.close()

    return jsonify({
        "message": "Password changed successfully"
    })