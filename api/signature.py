"""
腾讯会议企业版 API HMAC-SHA256 签名模块
参考: https://cloud.tencent.com/document/product/1095/42418
"""
import base64
import hashlib
import hmac
import json
import random
import time
import uuid
from typing import Any, Dict, Optional


class TencentMeetingSigner:
    """生成腾讯会议 REST API 请求签名与标准请求头"""

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        app_id: str,
        sdk_id: str,
        operator_id: str = "",
        operator_id_type: int = 1,
    ):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.sdk_id = sdk_id
        self.operator_id = operator_id
        self.operator_id_type = operator_id_type

    def _body_hash(self, body: Optional[str]) -> str:
        payload = body or ""
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def sign(
        self,
        method: str,
        uri: str,
        body: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        nonce: Optional[int] = None,
    ) -> Dict[str, str]:
        ts = timestamp or int(time.time())
        nc = nonce or random.randint(1, 2**31 - 1)
        body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body else ""
        body_hash = self._body_hash(body_str)

        header_string = (
            f"X-TC-Key={self.secret_id}&"
            f"X-TC-Nonce={nc}&"
            f"X-TC-Timestamp={ts}"
        )
        string_to_sign = f"{method.upper()}\n{header_string}\n{uri}\n{body_hash}"

        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "AppId": self.app_id,
            "SdkId": self.sdk_id,
            "X-TC-Key": self.secret_id,
            "X-TC-Timestamp": str(ts),
            "X-TC-Nonce": str(nc),
            "X-TC-Signature": signature,
            "X-TC-Registered": "1",
            "X-Request-Id": str(uuid.uuid4()),
        }
        if self.operator_id:
            headers["X-TC-Operator-Id"] = self.operator_id
            headers["X-TC-Operator-Id-Type"] = str(self.operator_id_type)

        return headers
