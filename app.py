from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = "agrihealth-beginner-demo"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "agrihealth.db"
UPLOAD_DIR = Path("/tmp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE,
            farmer TEXT,
            crop TEXT,
            country TEXT,
            state TEXT,
            district TEXT,
            village TEXT,
            stage TEXT,
            moisture INTEGER,
            diagnosis TEXT,
            confidence INTEGER,
            risk TEXT,
            status TEXT,
            image TEXT,
            action TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            message TEXT,
            level TEXT,
            created_at TEXT,
            is_read INTEGER DEFAULT 0
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    if count == 0:
        sample = [
            ("AG-1001","Rahul Patil","Tomato","India","Maharashtra","Nagpur","Katol","Flowering",45,"Early Blight",87,"HIGH","Pending Review","","Inspect lower leaves and follow IPM","2026-08-22 09:15"),
            ("AG-1002","Priya Sharma","Cotton","India","Maharashtra","Wardha","Seloo","Vegetative",62,"Healthy / Low Risk",91,"LOW","Resolved","","Continue field monitoring","2026-08-22 11:30"),
            ("AG-1003","Amit Verma","Soybean","India","Madhya Pradesh","Indore","Depalpur","Flowering",82,"Fungal Disease Risk",78,"MEDIUM","Pending Review","","Improve airflow and monitor lesions","2026-08-23 08:45"),
            ("AG-1004","Suresh Pawar","Maize","India","Maharashtra","Nagpur","Ramtek","Vegetative",29,"Moisture Stress Risk",84,"HIGH","Pending Review","","Irrigate according to soil and rainfall conditions","2026-08-23 14:10"),
            ("AG-1005","Neha Singh","Wheat","India","Punjab","Ludhiana","Khanna","Maturity",55,"Healthy / Low Risk",93,"LOW","Resolved","","Continue scouting until harvest","2026-08-24 10:05"),
        ]
        conn.executemany("""
            INSERT INTO cases
            (case_id,farmer,crop,country,state,district,village,stage,moisture,diagnosis,confidence,risk,status,image,action,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, sample)

    alert_count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    if alert_count == 0:
        alerts = [
            ("Early Blight Risk Detected","Tomato cases require field inspection and follow-up.","HIGH","2026-08-22 09:15"),
            ("Rainfall Expected","Review irrigation decisions when rainfall is forecast.","MEDIUM","2026-08-23 07:30"),
            ("Pest Monitoring","Continue scouting in fields with increasing pest pressure.","LOW","2026-08-24 08:00"),
        ]
        conn.executemany(
            "INSERT INTO alerts(title,message,level,created_at) VALUES (?,?,?,?)",
            alerts
        )
    conn.commit()
    conn.close()


CROP_PROFILES = {
    "Tomato": ("Early Blight", 87, "Inspect lower leaves, improve airflow and follow IPM."),
    "Cotton": ("Aphid / Pest Pressure", 82, "Scout leaf undersides and use threshold-based IPM."),
    "Soybean": ("Fungal Disease Risk", 80, "Monitor lesions, canopy humidity and field drainage."),
    "Maize": ("Moisture / Leaf Stress", 84, "Check soil moisture and adjust irrigation to rainfall."),
    "Wheat": ("Leaf Disease Risk", 81, "Scout lower canopy and monitor weather-driven disease pressure."),
    "Groundnut": ("Leaf Spot Risk", 79, "Monitor leaf spots and maintain balanced moisture."),
}


def analyze_crop(crop, stage, moisture):
    crop = crop.strip().title() if crop else "Tomato"
    stage = stage.strip().title() if stage else "Flowering"
    try:
        moisture = max(0, min(100, int(moisture)))
    except (TypeError, ValueError):
        moisture = 50

    disease, base_conf, action = CROP_PROFILES.get(
        crop,
        ("General Crop Stress", 70, "Inspect the plant closely and seek expert validation if symptoms persist.")
    )

    if moisture < 25:
        risk = "HIGH"
        diagnosis = "Severe Moisture Stress Risk"
        confidence = min(96, base_conf + 5)
        action = "Check soil moisture immediately and irrigate only after considering rainfall forecast."
    elif moisture < 45:
        risk = "MEDIUM"
        diagnosis = f"{disease} + Moisture Stress"
        confidence = min(95, base_conf)
    elif moisture <= 70:
        risk = "LOW"
        diagnosis = "Healthy / Low Risk" if crop in CROP_PROFILES else "Low Current Stress"
        confidence = min(96, base_conf + 4)
    elif moisture <= 85:
        risk = "MEDIUM"
        diagnosis = f"{disease} Risk"
        confidence = min(95, base_conf + 1)
        action = "Avoid unnecessary irrigation; increase scouting after humid or rainy periods."
    else:
        risk = "HIGH"
        diagnosis = f"{disease} + Excess Moisture Risk"
        confidence = min(96, base_conf + 3)
        action = "Check drainage and avoid prolonged leaf wetness."

    return {
        "crop": crop, "stage": stage, "moisture": moisture,
        "diagnosis": diagnosis, "confidence": confidence,
        "risk": risk, "action": action,
        "monitoring": [
            f"Observe symptoms at the {stage.lower()} stage.",
            "Record new photos during the next field visit.",
            "Check soil moisture and recent rainfall before irrigation."
        ],
        "precautions": [
            "Avoid spraying without confirming the problem.",
            "Prefer IPM and threshold-based decisions.",
            "Seek extension/expert validation for severe or unusual symptoms."
        ]
    }


def dashboard_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    high = conn.execute("SELECT COUNT(*) FROM cases WHERE risk='HIGH'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM cases WHERE status='Pending Review'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM cases WHERE status='Resolved'").fetchone()[0]
    conn.close()
    return {"total": total, "high": high, "pending": pending, "resolved": resolved}


@app.route("/")
def dashboard():
    conn = get_db()
    cases = conn.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 8").fetchall()
    alerts = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return render_template("dashboard.html", stats=dashboard_stats(), cases=cases, alerts=alerts)


@app.route("/diagnose", methods=["GET", "POST"])
def diagnose():
    if request.method == "POST":
        farmer = request.form.get("farmer", "").strip() or "Demo Farmer"
        crop = request.form.get("crop", "Tomato")
        country = request.form.get("country", "India")
        state = request.form.get("state", "")
        district = request.form.get("district", "")
        village = request.form.get("village", "")
        stage = request.form.get("stage", "Flowering")
        moisture = request.form.get("moisture", 50)
        image_path = ""

        image = request.files.get("image")
        if image and image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                flash("Please upload JPG, JPEG, PNG or WEBP.", "error")
                return redirect(url_for("diagnose"))
            filename = f"{uuid.uuid4().hex}{ext}"
            image.save(UPLOAD_DIR / filename)
            image_path = f"uploads/{filename}"

        result = analyze_crop(crop, stage, moisture)
        case_id = f"AG-{uuid.uuid4().hex[:6].upper()}"

        conn = get_db()
        conn.execute("""
            INSERT INTO cases
            (case_id,farmer,crop,country,state,district,village,stage,moisture,diagnosis,confidence,risk,status,image,action,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            case_id, farmer, result["crop"], country, state, district, village,
            result["stage"], result["moisture"], result["diagnosis"], result["confidence"],
            result["risk"], "Pending Review", image_path, result["action"],
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        conn.commit()
        conn.close()

        return render_template("result.html", result=result, case_id=case_id,
                               image_path=image_path, location=f"{district}, {state}, {country}")

    return render_template("diagnose.html")


@app.route("/cases")
def cases():
    conn = get_db()
    rows = conn.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("cases.html", cases=rows)


@app.route("/analytics")
def analytics():
    conn = get_db()
    crop_rows = conn.execute("""
        SELECT crop, COUNT(*) AS count
        FROM cases GROUP BY crop ORDER BY count DESC
    """).fetchall()
    risk_rows = conn.execute("""
        SELECT risk, COUNT(*) AS count
        FROM cases GROUP BY risk
    """).fetchall()
    disease_rows = conn.execute("""
        SELECT diagnosis, COUNT(*) AS count
        FROM cases GROUP BY diagnosis ORDER BY count DESC
    """).fetchall()
    conn.close()
    return render_template("analytics.html",
                           crop_rows=crop_rows, risk_rows=risk_rows, disease_rows=disease_rows)


@app.route("/map")
def hotspot_map():
    conn = get_db()
    rows = conn.execute("""
        SELECT state, district, crop, diagnosis, risk, COUNT(*) AS count
        FROM cases
        GROUP BY state, district, crop, diagnosis, risk
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return render_template("map.html", hotspots=rows)


@app.route("/recheck/<case_id>", methods=["POST"])
def recheck(case_id):
    moisture = request.form.get("moisture", 50)
    conn = get_db()
    row = conn.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
    if not row:
        conn.close()
        flash("Case not found.", "error")
        return redirect(url_for("cases"))

    result = analyze_crop(row["crop"], row["stage"], moisture)
    conn.execute("""
        UPDATE cases
        SET moisture=?, diagnosis=?, confidence=?, risk=?, action=?, status=?
        WHERE case_id=?
    """, (
        result["moisture"], result["diagnosis"], result["confidence"],
        result["risk"], result["action"], "Pending Review", case_id
    ))
    conn.commit()
    conn.close()

    next_check = datetime.now() + timedelta(hours=24 if result["risk"] == "LOW" else 12)
    flash(f"Recheck completed. Next suggested check: {next_check.strftime('%d %b %Y, %I:%M %p')}.", "success")
    return redirect(url_for("cases"))


@app.route("/assign-extension/<case_id>", methods=["POST"])
def assign_extension(case_id):
    conn = get_db()
    updated = conn.execute(
        "UPDATE cases SET status='Assigned to Extension' WHERE case_id=?",
        (case_id,)
    ).rowcount
    conn.commit()
    conn.close()
    flash(
        "Extension response assigned successfully." if updated else "Case not found.",
        "success" if updated else "error"
    )
    return redirect(url_for("cases"))


@app.route("/field-vault")
def field_vault():
    conn = get_db()
    rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("field_vault.html", cases=rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
