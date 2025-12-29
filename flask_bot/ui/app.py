import os
from flask import Flask, request, render_template, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Config (STRICT)
# -------------------------
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is not set")

FLASK_SECRET = os.environ.get("FLASK_SECRET")
if not FLASK_SECRET:
    raise RuntimeError("FLASK_SECRET is not set")

# -------------------------
# Flask & SQLAlchemy
# -------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET

engine = create_engine(
    DB_URL,
    echo=True,
    pool_pre_ping=True
)

Base = declarative_base()
Session = sessionmaker(bind=engine)

# -------------------------
# Model
# -------------------------
class BotTrigger(Base):
    __tablename__ = "triggers"
    id = Column(Integer, primary_key=True)
    trigger = Column(String(200), unique=True, nullable=False)
    response = Column(Text, nullable=False)

Base.metadata.create_all(engine)

# -------------------------
# Routes
# -------------------------
@app.route("/")
def dashboard():
    session = Session()
    triggers = session.query(BotTrigger).order_by(BotTrigger.id).all()
    session.close()
    return render_template("index.html", triggers=triggers)

# ADD
@app.route("/trigger/add", methods=["POST"])
def add_trigger():
    trig = request.form.get("trigger", "").strip()
    resp = request.form.get("response", "").strip()

    if not trig or not resp:
        flash("Trigger and Response are required.", "danger")
        return redirect(url_for("dashboard"))

    session = Session()
    try:
        exists = session.query(BotTrigger).filter(
            func.lower(BotTrigger.trigger) == trig.lower()
        ).first()

        if exists:
            flash("Trigger already exists.", "warning")
            return redirect(url_for("dashboard"))

        session.add(BotTrigger(trigger=trig, response=resp))
        session.commit()
        flash("Trigger added.", "success")

    except Exception as e:
        session.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        session.close()

    return redirect(url_for("dashboard"))
#EDIT
@app.route("/trigger/edit/<int:id>", methods=["POST"])
def edit_trigger(id):
    trig = request.form.get("trigger", "").strip()
    resp = request.form.get("response", "").strip()

    if not trig or not resp:
        flash("Trigger and Response are required.", "danger")
        return redirect(url_for("dashboard"))

    session = Session()
    try:
        obj = session.get(BotTrigger, id)
        if not obj:
            flash("Trigger not found.", "danger")
            return redirect(url_for("dashboard"))

        obj.trigger = trig
        obj.response = resp
        session.commit()
        flash("Trigger updated.", "success")

    except Exception as e:
        session.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        session.close()

    return redirect(url_for("dashboard"))

# DELETE
@app.route("/trigger/delete/<int:id>", methods=["GET","POST"])
def delete_trigger(id):
    session = Session()
    try:
        obj = session.get(BotTrigger, id)
        if obj:
            session.delete(obj)
            session.commit()
            flash("Trigger deleted.", "success")
    except Exception as e:
        session.rollback()
        flash(f"Error: {e}", "danger")
    finally:
        session.close()

    return redirect(url_for("dashboard"))
