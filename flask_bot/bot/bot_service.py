import os
import time
import requests
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# Config
# -------------------------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///bot.db")
POLL_INTERVAL = 1

# -------------------------
# Database
# -------------------------
engine = create_engine(DB_URL, echo=True)
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
    url = f"{TELEGRAM_API_URL}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
        return resp.ok
    except Exception as e:
        print("send_message error:", e)
        return False

# -------------------------
# Polling loop
# -------------------------
def poll_telegram():
    print("Telegram polling thread started.")
    last_update_id = None
    while True:
        try:
            params = {}
            if last_update_id is not None:
                params["offset"] = last_update_id + 1
            resp = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params, timeout=30)
            if not resp.ok:
                print(f"[ERROR] getUpdates failed: {resp.status_code}")
                time.sleep(POLL_INTERVAL)
                continue

            results = resp.json().get("result", [])
            for update in results:
                last_update_id = update.get("update_id", last_update_id)
                message = update.get("message")
                if not message: continue
                text = message.get("text", "").strip()
                chat_id = message.get("chat", {}).get("id")
                if not text or not chat_id: continue
                print(f"[INFO] Received: {text} from {chat_id}")

                session = Session()
                try:
                    trigger_entry = session.query(BotTrigger)\
                                           .filter(func.lower(BotTrigger.trigger) == text.lower())\
                                           .first()
                    if trigger_entry:
                        print(f"[INFO] Trigger matched: {trigger_entry.response}")
                        send_message(chat_id, trigger_entry.response)
                finally:
                    session.close()
        except Exception as e:
            print(f"[ERROR] Polling exception: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    poll_telegram()
