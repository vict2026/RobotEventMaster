import time
import hashlib
import hmac
import requests
from config import TENCENT_MEETING

def _sign(params: dict) -> str:
    secret_key = TENCENT_MEETING["secret_key"]
    string_to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(secret_key.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()

def create_meeting(subject: str, start_time: int, duration: int = 240):
    params = {
        "action": "CreateMeeting",
        "secretId": TENCENT_MEETING["secret_id"],
        "timestamp": str(int(time.time())),
        "nonce": str(int(time.time() * 1000)),
        "appid": TENCENT_MEETING["appid"],
    }
    params["signature"] = _sign(params)
    
    data = {
        "subject": subject,
        "start_time": start_time,
        "duration": duration,
        "auto_record_type": 1,   # 自动云录制
        "host_userid": TENCENT_MEETING["host_userid"],
    }
    resp = requests.post("https://api.meeting.qq.com/v1/meetings", json=data, params=params)
    return resp.json()