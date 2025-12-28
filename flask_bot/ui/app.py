import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Config
# -------------------------
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///bot.db")
FLASK_SECRET = os.environ.get("FLASK_SECRET", "dev_secret_key")

# -------------------------
# Flask & SQLAlchemy
# -------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET

engine = create_engine(DB_URL, echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class BotTrigger(Base):
    __tablename__ = "triggers"
    id = Column(Integer, primary_key=True)
    trigger = Column(String(200), unique=True, nullable=False)
    response = Column(Text, nullable=False)

Base.metadata.create_all(engine)

# -------------------------
# CRUD Routes (UI + API)
# -------------------------
@app.route("/")
def dashboard():
    session = Session()
    triggers = session.query(BotTrigger).order_by(BotTrigger.id).all()
    session.close()
    return render_template("index.html", triggers=triggers)

@app.route("/trigger/add", methods=["POST"])
def add_trigger():
    data = request.form
    trig = data.get("trigger", "").strip()
    resp = data.get("response", "").strip()
    if not trig or not resp:
        flash("Trigger and Response are required.", "danger")
        return redirect(url_for("dashboard"))

    session = Session()
    try:
        exists = session.query(BotTrigger).filter(func.lower(BotTrigger.trigger) == trig.lower()).first()
        if exists:
            flash("Trigger already exists.", "warning")
            return redirect(url_for("dashboard"))
        new = BotTrigger(trigger=trig, response=resp)
        session.add(new)
        session.commit()
        flash("Trigger added.", "success")
    except Exception as e:
        session.rollback()
        flash(f"Error adding trigger: {e}", "danger")
    finally:
        session.close()
    return redirect(url_for("dashboard"))
