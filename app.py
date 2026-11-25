from flask import Flask, render_template, request, send_file, redirect, session
import os, json
from ultralytics import YOLO
from PIL import Image
from utils.report import generate_report
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "static/results"
REPORT_PATH = "static/damage_report.pdf"
USER_FILE = "users.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

model = YOLO("model/best.pt")

# -------------------------------
# 📦 USER STORAGE
# -------------------------------
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# -------------------------------
# 🚗 VALIDATION
# -------------------------------
def is_vehicle_present(results, model):
    vehicle_keywords = ["car", "truck", "bus", "vehicle"]
    for r in results:
        if r.boxes is not None:
            for cls in r.boxes.cls:
                label = model.names[int(cls)].lower()
                if any(k in label for k in vehicle_keywords):
                    return True
    return False

def has_any_detection(results):
    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            return True
    return False

# -------------------------------
# 💰 COST LOGIC
# -------------------------------
damage_cost = {
    "scratch": {"min": 500, "max": 3000},
    "dent": {"min": 1500, "max": 8000},
    "crack": {"min": 2000, "max": 7000},
    "glass shatter": {"min": 4000, "max": 12000},
    "lamp broken": {"min": 3000, "max": 9000},
    "tire flat": {"min": 1000, "max": 4000}
}

PART_MAPPING = {
    "scratch": "Body",
    "dent": "Body",
    "crack": "Body",
    "glass shatter": "Windshield",
    "lamp broken": "Lights",
    "tire flat": "Wheels"
}

def calculate_precise_cost(label, box, img_w, img_h):
    x1, y1, x2, y2 = box
    area = (x2 - x1) * (y2 - y1)
    ratio = area / (img_w * img_h)

    base = damage_cost.get(label, {"min": 1000, "max": 3000})
    normalized = min(ratio * 5, 1)
    cost = base["min"] + (base["max"] - base["min"]) * normalized

    return int(cost), ratio

def apply_density_factor(total, cost):
    if total > 5:
        return int(cost * 1.2)
    elif total > 2:
        return int(cost * 1.1)
    return cost

def estimate_precise_cost(results, model, img_w, img_h):
    total_cost, damage_list, total_damages = 0, [], 0

    for r in results:
        if r.boxes is not None:
            total_damages += len(r.boxes)

    for r in results:
        if r.boxes is not None:
            for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
                label = model.names[int(cls)]
                box = box.tolist()

                cost, ratio = calculate_precise_cost(label, box, img_w, img_h)
                cost = apply_density_factor(total_damages, cost)

                damage_list.append({
                    "label": label,
                    "part": PART_MAPPING.get(label, "Other"),
                    "ratio": round(ratio, 4),
                    "cost": cost
                })

                total_cost += cost

    return total_cost, damage_list, total_damages

# -------------------------------
# 🔥 SEVERITY
# -------------------------------
def calculate_severity(damages):
    if not damages:
        return "No Damage"

    avg_ratio = sum(d["ratio"] for d in damages) / len(damages)

    if avg_ratio < 0.02:
        return "Minor"
    elif avg_ratio < 0.08:
        return "Moderate"
    else:
        return "Severe"

# -------------------------------
# 🚨 ENGINE DAMAGE
# -------------------------------
def estimate_engine_damage(results_data):
    front = results_data.get("front", {})

    if not front:
        return {"status": "No Risk", "cost": 0}

    severity = front.get("severity", "Minor")
    damages = front.get("details", [])

    critical_hits = sum(1 for d in damages if d["label"] in ["crack", "dent"])

    if severity == "Severe" and critical_hits > 2:
        return {"status": "High", "cost": 20000}
    elif severity == "Moderate":
        return {"status": "Medium", "cost": 8000}
    else:
        return {"status": "Low", "cost": 2000}

# -------------------------------
# 🔐 AUTH
# -------------------------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_users()
        email = request.form["email"]

        if email in users:
            return render_template("register.html", error="User exists")

        users[email] = {
            "name": request.form["name"],
            "email": email,
            "password": generate_password_hash(request.form["password"]),
            "contact_number": request.form["phone"],
            "vehicle_id": request.form["vehicle_id"],
            "car_brand": request.form["car_brand"],
            "model": request.form["model"],
            "address": request.form["address"]
        }

        save_users(users)
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        email = request.form["email"]
        password = request.form["password"]

        if email in users and check_password_hash(users[email]["password"], password):
            session["user"] = email
            return redirect("/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------------------
# 👤 PROFILE
# -------------------------------
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    users = load_users()
    return render_template("profile.html", user_info=users[session["user"]])

# -------------------------------
# 🚀 DASHBOARD
# -------------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

# -------------------------------
# 🔍 PREDICT
# -------------------------------
@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return redirect("/login")

    views = ["front", "rear", "left", "right"]
    results_data = {}

    for view in views:
        file = request.files.get(view)

        if file and file.filename != "":
            upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
            result_path = os.path.join(RESULT_FOLDER, file.filename)

            file.save(upload_path)
            results = model(upload_path)

            if not is_vehicle_present(results, model):
                if not has_any_detection(results):
                    return render_template("index.html", error="Invalid car image")

            for r in results:
                r.save(filename=result_path)

            img = Image.open(upload_path)
            img_w, img_h = img.size

            cost, damage_details, count = estimate_precise_cost(
                results, model, img_w, img_h
            )

            results_data[view] = {
                "count": count,
                "image": file.filename,
                "cost": cost,
                "details": damage_details
            }

    # Add severity
    for view in results_data:
        results_data[view]["severity"] = calculate_severity(
            results_data[view]["details"]
        )

    # Engine damage
    engine_damage = estimate_engine_damage(results_data)

    total_cost = sum(d['cost'] for d in results_data.values())
    total_cost += engine_damage["cost"]

    # User info
    users = load_users()
    user_info = users[session["user"]]

    # Generate report
    generate_report(
        results_data,
        REPORT_PATH,
        user_info=user_info,
        engine_damage=engine_damage,
        total_cost=total_cost
    )

    return render_template(
        "result.html",
        results=results_data,
        total_cost=total_cost,
        engine_damage=engine_damage
    )

@app.route("/download-report")
def download_report():
    return send_file(REPORT_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)