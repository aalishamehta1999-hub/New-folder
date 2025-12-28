import time
import json
from datetime import datetime


def run_send_job(params, logger):

    # Safety: kill legacy csv
    params.pop('csv', None)

    logger(f"DEBUG params keys: {list(params.keys())}")

    rows = params.get("edited_rows")
    if not rows:
        logger("❌ No rows received")
        return

    # Remove header if present
    if isinstance(rows[0][1], str) and rows[0][1].lower().startswith("phone"):
        rows = rows[1:]

    logger(f"✅ {len(rows)} rows loaded")

    with open(params["messages_db"], "r", encoding="utf-8") as f:
        messages = json.load(f)[params["template_key"]]

    name_col = params.get("name_col", 1) - 1
    phone_col = params.get("phone_col", 2) - 1
    flag_col = params.get("flag_col", 3) - 1
    country_code = params.get("country_code", "+91")
    wait_time = params.get("wait_time", 5)

    for msg in messages:
        send_time = datetime.fromisoformat(msg["send_datetime"])
        delay = (send_time - datetime.now()).total_seconds()

        if delay > 0:
            logger(f"⏳ Waiting until {send_time}")
            time.sleep(delay)

        logger("📨 Sending batch")

        for row in rows:
            try:
                flag = str(row[flag_col]).strip().lower()
                if flag not in ('1', 'true', 'yes', 'y'):
                    continue

                name = str(row[name_col]).strip()
                phone = str(row[phone_col]).strip()

                if not phone.startswith('+'):
                    phone = country_code + phone

                text = msg["template"].replace("{Name}", name)

                logger(f"📤 {phone} → {text}")

                # 🔥 Replace this with pywhatkit later
                time.sleep(wait_time)

            except Exception as e:
                logger(f"❌ Row error: {e}")

    logger("✅ All messages sent")
