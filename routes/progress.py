from flask import Blueprint, request, jsonify, g
from db.database import get_db
from middleware.auth import login_required
from datetime import date

prog_bp = Blueprint("progress", __name__)

# ── DSA ──
@prog_bp.route("/dsa", methods=["GET"])
@login_required
def get_dsa():
    db = get_db()
    rows = db.execute("SELECT topic_index, problem_index FROM dsa_solved WHERE user_id=?", (g.user["id"],)).fetchall()
    db.close()
    result = {}
    for r in rows:
        ti, pi = str(r["topic_index"]), str(r["problem_index"])
        if ti not in result: result[ti] = {}
        result[ti][pi] = True
    return jsonify(result)

@prog_bp.route("/dsa/toggle", methods=["POST"])
@login_required
def toggle_dsa():
    d = request.get_json()
    ti, pi = d.get("topic_index"), d.get("problem_index")
    if ti is None or pi is None: return jsonify({"error":"topic_index and problem_index required"}), 400
    db = get_db()
    ex = db.execute("SELECT id FROM dsa_solved WHERE user_id=? AND topic_index=? AND problem_index=?",
                    (g.user["id"], ti, pi)).fetchone()
    if ex:
        db.execute("DELETE FROM dsa_solved WHERE id=?", (ex["id"],))
        solved = False
    else:
        db.execute("INSERT INTO dsa_solved (user_id, topic_index, problem_index) VALUES (?,?,?)",
                   (g.user["id"], ti, pi))
        solved = True
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM dsa_solved WHERE user_id=?", (g.user["id"],)).fetchone()[0]
    db.close()
    return jsonify({"solved": solved, "total": total})

# ── PROJECTS ──
@prog_bp.route("/projects", methods=["GET"])
@login_required
def get_projects():
    db = get_db()
    rows = db.execute("SELECT project_index, status FROM projects WHERE user_id=?", (g.user["id"],)).fetchall()
    db.close()
    return jsonify({str(r["project_index"]): r["status"] for r in rows})

@prog_bp.route("/projects/<int:idx>", methods=["PUT"])
@login_required
def update_project(idx):
    d = request.get_json()
    status = d.get("status","todo")
    if status not in ["todo","progress","done"]: return jsonify({"error":"Invalid status"}), 400
    db = get_db()
    db.execute("INSERT INTO projects (user_id, project_index, status) VALUES (?,?,?) ON CONFLICT(user_id, project_index) DO UPDATE SET status=?, updated_at=CURRENT_TIMESTAMP",
               (g.user["id"], idx, status, status))
    db.commit(); db.close()
    return jsonify({"status": status})

# ── CERTIFICATIONS ──
@prog_bp.route("/certs", methods=["GET"])
@login_required
def get_certs():
    db = get_db()
    rows = db.execute("SELECT cert_index FROM certifications WHERE user_id=?", (g.user["id"],)).fetchall()
    db.close()
    return jsonify({str(r["cert_index"]): True for r in rows})

@prog_bp.route("/certs/<int:idx>/toggle", methods=["POST"])
@login_required
def toggle_cert(idx):
    db = get_db()
    ex = db.execute("SELECT id FROM certifications WHERE user_id=? AND cert_index=?", (g.user["id"], idx)).fetchone()
    if ex:
        db.execute("DELETE FROM certifications WHERE id=?", (ex["id"],)); earned = False
    else:
        db.execute("INSERT INTO certifications (user_id, cert_index) VALUES (?,?)", (g.user["id"], idx)); earned = True
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (g.user["id"],)).fetchone()[0]
    db.close()
    return jsonify({"earned": earned, "total": total})

# ── SKILLS ──
@prog_bp.route("/skills", methods=["GET"])
@login_required
def get_skills():
    db = get_db()
    rows = db.execute("SELECT skill_key, skill_index, done FROM skills WHERE user_id=?", (g.user["id"],)).fetchall()
    db.close()
    result = {}
    for r in rows:
        if r["skill_key"] not in result: result[r["skill_key"]] = {}
        result[r["skill_key"]][str(r["skill_index"])] = bool(r["done"])
    return jsonify(result)

@prog_bp.route("/skills/toggle", methods=["POST"])
@login_required
def toggle_skill():
    d = request.get_json()
    key, idx = d.get("key"), d.get("index")
    db = get_db()
    ex = db.execute("SELECT id, done FROM skills WHERE user_id=? AND skill_key=? AND skill_index=?",
                    (g.user["id"], key, idx)).fetchone()
    if ex:
        new_done = 0 if ex["done"] else 1
        db.execute("UPDATE skills SET done=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_done, ex["id"]))
    else:
        db.execute("INSERT INTO skills (user_id, skill_key, skill_index, done) VALUES (?,?,?,1)", (g.user["id"], key, idx))
        new_done = 1
    db.commit(); db.close()
    return jsonify({"done": bool(new_done)})

# ── STREAK ──
@prog_bp.route("/streak", methods=["GET"])
@login_required
def get_streak():
    db = get_db()
    rows = db.execute("SELECT date FROM streak_log WHERE user_id=? ORDER BY date DESC LIMIT 60", (g.user["id"],)).fetchall()
    db.close()
    dates = [r["date"] for r in rows]
    # Calculate current streak
    from datetime import datetime, timedelta
    today = date.today()
    streak = 0
    for i in range(60):
        d = (today - timedelta(days=i)).isoformat()
        if d in dates: streak += 1
        elif i > 0: break
    return jsonify({"dates": dates, "streak": streak, "total_days": len(dates)})

@prog_bp.route("/streak/mark", methods=["POST"])
@login_required
def mark_streak():
    today = date.today().isoformat()
    db = get_db()
    try:
        db.execute("INSERT INTO streak_log (user_id, date) VALUES (?,?)", (g.user["id"], today))
        db.commit()
        marked = True
    except: marked = False
    rows = db.execute("SELECT date FROM streak_log WHERE user_id=? ORDER BY date DESC LIMIT 60", (g.user["id"],)).fetchall()
    dates = [r["date"] for r in rows]
    from datetime import datetime, timedelta
    streak = 0
    for i in range(60):
        d = (date.today() - timedelta(days=i)).isoformat()
        if d in dates: streak += 1
        elif i > 0: break
    db.close()
    return jsonify({"marked": marked, "streak": streak, "dates": dates})

# ── GENERIC KEY-VALUE PROGRESS (daily checks, weekly tasks, companies etc.) ──
@prog_bp.route("/kv/<key>", methods=["GET"])
@login_required
def kv_get(key):
    db = get_db()
    row = db.execute("SELECT value FROM user_progress WHERE user_id=? AND key=?", (g.user["id"], key)).fetchone()
    db.close()
    return jsonify({"value": row["value"] if row else None})

@prog_bp.route("/kv/<key>", methods=["PUT"])
@login_required
def kv_set(key):
    import json
    value = request.get_json().get("value","")
    if not isinstance(value, str): value = json.dumps(value)
    db = get_db()
    db.execute("INSERT INTO user_progress (user_id, key, value) VALUES (?,?,?) ON CONFLICT(user_id, key) DO UPDATE SET value=?, updated_at=CURRENT_TIMESTAMP",
               (g.user["id"], key, value, value))
    db.commit(); db.close()
    return jsonify({"saved": True})

# ── NOTES ──
@prog_bp.route("/notes", methods=["GET"])
@login_required
def get_notes():
    db = get_db()
    rows = db.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC", (g.user["id"],)).fetchall()
    db.close()
    return jsonify({"notes": [dict(r) for r in rows]})

@prog_bp.route("/notes", methods=["POST"])
@login_required
def add_note():
    d = request.get_json()
    db = get_db()
    c = db.execute("INSERT INTO notes (user_id, title, content, color) VALUES (?,?,?,?)",
                   (g.user["id"], d.get("title","Untitled"), d.get("content",""), d.get("color","#3B82F6")))
    db.commit(); nid = c.lastrowid; db.close()
    return jsonify({"id": nid, "message": "Note saved"}), 201

@prog_bp.route("/notes/<int:nid>", methods=["DELETE"])
@login_required
def del_note(nid):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, g.user["id"]))
    db.commit(); db.close()
    return jsonify({"deleted": True})

# ── STATS SUMMARY ──
@prog_bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    uid = g.user["id"]
    db = get_db()
    dsa_total = db.execute("SELECT COUNT(*) FROM dsa_solved WHERE user_id=?", (uid,)).fetchone()[0]
    proj_done = db.execute("SELECT COUNT(*) FROM projects WHERE user_id=? AND status='done'", (uid,)).fetchone()[0]
    cert_done = db.execute("SELECT COUNT(*) FROM certifications WHERE user_id=?", (uid,)).fetchone()[0]
    skill_done = db.execute("SELECT COUNT(*) FROM skills WHERE user_id=? AND done=1", (uid,)).fetchone()[0]
    streak_total = db.execute("SELECT COUNT(*) FROM streak_log WHERE user_id=?", (uid,)).fetchone()[0]
    db.close()
    return jsonify({"dsa":dsa_total,"projects":proj_done,"certs":cert_done,"skills":skill_done,"streak_days":streak_total})