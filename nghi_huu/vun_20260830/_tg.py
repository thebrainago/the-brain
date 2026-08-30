import json, requests
from pathlib import Path
lab = Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
k = json.loads((lab/"config"/"api_keys.json").read_text(encoding="utf-8-sig"))
tok = k["telegram_bot_token"]
def call(m, data=None):
    try:
        r = requests.post("https://api.telegram.org/bot" + tok + "/" + m, data=data, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
me = call("getMe")
print("getMe:", json.dumps(me, ensure_ascii=False)[:300])
up = call("getUpdates")
print("getUpdates:", json.dumps(up, ensure_ascii=False)[:600])
