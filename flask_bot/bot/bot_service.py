import os
import requests
from flask import Flask, request, abort
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Config
# -------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
TELEGRAM_SECRET = os.environ.get("TELEGRAM_SECRET")  # buat verify webhook

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
if not TELEGRAM_SECRET:
    raise RuntimeError("TELEGRAM_SECRET is not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# -------------------------
# App & DB
# -------------------------
app = Flask(__name__)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

Base = declarative_base()
Session = sessionmaker(bind=engine)

class BotTrigger(Base):
    __tablename__ = "triggers"
    id = Column(Integer, primary_key=True)
    trigger = Column(String(200), unique=True, nullable=False)
    response = Column(Text, nullable=False)

# -------------------------
# Telegram Helper
# -------------------------
def send_message(chat_id: int, text: str):
    try:
        resp = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        return resp.ok
    except Exception as e:
        print("[ERROR] send_message:", e)
        return False

# -------------------------
# Webhook Endpoint
# -------------------------
@app.post("/telegram/webhook")
def telegram_webhook():

    # 1️⃣ SECURITY: verify telegram secret
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != TELEGRAM_SECRET:
        abort(403)

    data = request.get_json(silent=True)
    if not data:
        return "ok"

    message = data.get("message")
    if not message:
        return "ok"

    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")

    if not text or not chat_id:
        return "ok"

    print(f"[INFO] Incoming message: {text} from {chat_id}")

    # 2️⃣ DB lookup (FAST, blocking < 50ms)
    session = Session()
    try:
        trigger_entry = (
            session.query(BotTrigger)
            .filter(func.lower(BotTrigger.trigger) == text.lower())
            .first()
        )

        if trigger_entry:
            send_message(chat_id, trigger_entry.response)

    except Exception as e:
        print("[ERROR] webhook processing:", e)
    finally:
        session.close()

    # 3️⃣ IMPORTANT: ALWAYS return 200 FAST
    return "ok"
