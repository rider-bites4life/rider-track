from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import random
import os

app = Flask(__name__)
# CORS zaroori hai taake GitHub Pages se request block na ho
CORS(app)

# Database configuration - Koyeb ke liye /tmp folder zaroori hai
db_path = os.path.join('/tmp', 'rider_system_final.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20)) 
    last_device = db.Column(db.String(255), default="No Login Yet")

class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(10), unique=True)
    status = db.Column(db.String(50), default="Available")
    device_info = db.Column(db.String(255), default="Not Registered")
    r_time = db.Column(db.String(50), default="--") 
    a_time = db.Column(db.String(50), default="--") 
    last_click_dt = db.Column(db.DateTime, default=datetime.utcnow)
    ring_status = db.Column(db.String(20), default="idle")

# --- Database Initialization ---
with app.app_context():
    db.create_all()
    # Default super admin agar pehle se nahi hai
    if not User.query.filter_by(role='superadmin').first():
        db.session.add(User(email="super", password="4343", role="superadmin"))
        db.session.commit()

# --- ADMIN MANAGEMENT ROUTES (YE MISSING THAY) ---

@app.route('/add_admin', methods=['POST'])
def add_admin():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing data"}), 400
    new_admin = User(email=data['email'], password=data['password'], role='admin')
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/get_admins', methods=['GET'])
def get_admins():
    admins = User.query.filter_by(role='admin').all()
    return jsonify([{"id": a.id, "email": a.email, "device": a.last_device} for a in admins])

@app.route('/delete_admin/<int:id>', methods=['DELETE'])
def delete_admin(id):
    u = User.query.get(id)
    if u:
        db.session.delete(u)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Admin not found"}), 404

# --- RIDER & SYSTEM ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "Online", "message": "Bites4Life API is Running!"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u = User.query.filter_by(email=data['email'], password=data['password']).first()
    if u:
        u.last_device = request.headers.get('User-Agent', 'Web Browser')
        db.session.commit()
        return jsonify({"role": u.role, "email": u.email, "success": True})
    return jsonify({"error": "Invalid Credentials"}), 401

@app.route('/get_riders', methods=['GET'])
def get_riders():
    riders = Rider.query.all()
    return jsonify([{
        "name": r.name, 
        "code": r.code, 
        "status": r.status, 
        "r_time": r.r_time, 
        "a_time": r.a_time, 
        "device": r.device_info,
        "ring_status": r.ring_status
    } for r in riders])

@app.route('/add_rider', methods=['POST'])
def add_rider():
    code = str(random.randint(1000, 9999))
    db.session.add(Rider(name=request.json['name'], code=code))
    db.session.commit()
    return jsonify({"code": code, "success": True})

@app.route('/delete_rider/<code>', methods=['DELETE'])
def delete_rider(code):
    r = Rider.query.filter_by(code=code).first()
    if r:
        db.session.delete(r)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Rider not found"}), 404

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    r = Rider.query.filter_by(code=data['code']).first()
    if not r: return jsonify({"error": "Invalid Code"}), 404
    r.status = data['status']
    r.r_time = datetime.now().strftime("%I:%M %p")
    r.ring_status = "idle"
    db.session.commit()
    return jsonify({"success": True})

@app.route('/admin/on_route', methods=['POST'])
def set_on_route():
    data = request.json
    r = Rider.query.filter_by(code=data['code']).first()
    if r:
        r.status = "On Route"
        r.a_time = datetime.now().strftime("%I:%M %p")
        r.ring_status = "idle"
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Rider not found"}), 404

@app.route('/admin/ring_rider', methods=['POST'])
def ring_rider():
    data = request.json
    r = Rider.query.filter_by(code=data['code']).first()
    if r:
        r.ring_status = "ringing"
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Rider not found"}), 404

# --- Koyeb Specific Port Configuration ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
