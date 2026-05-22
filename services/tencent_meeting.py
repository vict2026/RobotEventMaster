"""
腾讯会议企业版 API 客户端
支持: CreateMeeting, 云录制, RemoveParticipant, MoveWaitingRoom 等
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

import config
from api.signature import TencentMeetingSigner
from database.db import get_session, write_audit_log
from database.models import MeetingLog

logger = logging.getLogger(__name__)


class TencentMeetingClient:
    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        cfg = cfg or config.TENCENT_MEETING
        self.base_url = cfg["base_url"].rstrip("/")
        self.signer = TencentMeetingSigner(
            secret_id=cfg["secret_id"],
            secret_key=cfg["secret_key"],
            app_id=cfg["app_id"],
            sdk_id=cfg["sdk_id"],
            operator_id=cfg.get("operator_id", ""),
            operator_id_type=cfg.get("operator_id_type", 1),
        )
        self._session = requests.Session()

    def _request(
        self,
        method: str,
        uri: str,
        body: Optional[Dict[str, Any]] = None,
        action: str = "api_call",
    ) -> Dict[str, Any]:
        headers = self.signer.sign(method, uri, body)
        url = f"{self.base_url}{uri}"
        body_str = None
        if body is not None:
            import json
            body_str = json.dumps(body, ensure_ascii=False)

        try:
            resp = self._session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=body_str.encode("utf-8") if body_str else None,
                timeout=30,
            )
            data = resp.json() if resp.content else {}
            success = resp.status_code in (200, 201)
            self._log_meeting_action(
                action=action,
                meeting_id=data.get("meeting_id") or data.get("meeting_info_list", [{}])[0].get("meeting_id", ""),
                request_payload=body,
                response_payload={"status_code": resp.status_code, "body": data},
                success=success,
                error_message=None if success else data.get("error_info", resp.text),
            )
            write_audit_log(action=f"meeting.{action}", resource=uri, detail={"status": resp.status_code})
            if not success:
                logger.error("Tencent Meeting API error [%s]: %s", action, data)
            return {"success": success, "status_code": resp.status_code, "data": data}
        except requests.RequestException as exc:
            self._log_meeting_action(
                action=action,
                request_payload=body,
                response_payload={},
                success=False,
                error_message=str(exc),
            )
            write_audit_log(action=f"meeting.{action}_error", resource=uri, detail={"error": str(exc)})
            logger.exception("Tencent Meeting request failed: %s", action)
            return {"success": False, "error": str(exc)}

    def _log_meeting_action(self, **kwargs):
        with get_session() as session:
            log = MeetingLog(
                meeting_id=kwargs.get("meeting_id", ""),
                meeting_code=kwargs.get("meeting_code", ""),
                action=kwargs.get("action", ""),
                participant_id=kwargs.get("participant_id"),
                participant_name=kwargs.get("participant_name"),
                request_payload=kwargs.get("request_payload"),
                response_payload=kwargs.get("response_payload"),
                success=kwargs.get("success", True),
                error_message=kwargs.get("error_message"),
            )
            session.add(log)

    # ── 会议管理 ──────────────────────────────────────────────────────────────

    def create_meeting(
        self,
        subject: str,
        start_time: Optional[datetime] = None,
        duration_min: int = 120,
        password: str = "",
        enable_waiting_room: bool = True,
        auto_record: bool = True,
    ) -> Dict[str, Any]:
        """创建会议 (CreateMeeting)"""
        start = start_time or datetime.now(timezone.utc)
        end = start + timedelta(minutes=duration_min)
        body = {
            "userid": config.TENCENT_MEETING.get("operator_id", ""),
            "instanceid": 1,
            "subject": subject,
            "type": 0,
            "start_time": str(int(start.timestamp())),
            "end_time": str(int(end.timestamp())),
            "password": password,
            "settings": {
                "auto_in_waiting_room": enable_waiting_room,
                "allow_in_before_host": True,
                "auto_record_type": "cloud" if auto_record else "none",
            },
        }
        return self._request("POST", "/v1/meetings", body, action="create_meeting")

    def cancel_meeting(self, meeting_id: str, reason: str = "") -> Dict[str, Any]:
        body = {"reason_code": 1, "reason_detail": reason or "赛事结束取消"}
        return self._request("POST", f"/v1/meetings/{meeting_id}/cancel", body, action="cancel_meeting")

    def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/meetings/{meeting_id}", action="get_meeting_info")

    # ── 参会者管理 ────────────────────────────────────────────────────────────

    def remove_participant(
        self,
        meeting_id: str,
        participant_id: str,
        participant_name: str = "",
        reason: str = "未授权人员",
    ) -> Dict[str, Any]:
        """移出参会者 (RemoveParticipant)"""
        body = {
            "operator_id": config.TENCENT_MEETING.get("operator_id", ""),
            "operator_id_type": config.TENCENT_MEETING.get("operator_id_type", 1),
            "instanceid": 1,
            "to_operator_id": participant_id,
            "to_operator_id_type": 4,
            "reason": reason,
        }
        result = self._request(
            "POST",
            f"/v1/meetings/{meeting_id}/kickout",
            body,
            action="remove_participant",
        )
        with get_session() as session:
            session.add(
                MeetingLog(
                    meeting_id=meeting_id,
                    action="remove_participant",
                    participant_id=participant_id,
                    participant_name=participant_name,
                    request_payload=body,
                    response_payload=result,
                    success=result.get("success", False),
                )
            )
        return result

    def move_to_waiting_room(
        self,
        meeting_id: str,
        participant_id: str,
        participant_name: str = "",
    ) -> Dict[str, Any]:
        """移至等候室 (MoveWaitingRoom)"""
        body = {
            "operator_id": config.TENCENT_MEETING.get("operator_id", ""),
            "operator_id_type": config.TENCENT_MEETING.get("operator_id_type", 1),
            "instanceid": 1,
            "to_operator_id": participant_id,
            "to_operator_id_type": 4,
        }
        return self._request(
            "POST",
            f"/v1/meetings/{meeting_id}/waiting-room/move-in",
            body,
            action="move_waiting_room",
        )

    def admit_from_waiting_room(
        self,
        meeting_id: str,
        participant_id: str,
    ) -> Dict[str, Any]:
        body = {
            "operator_id": config.TENCENT_MEETING.get("operator_id", ""),
            "operator_id_type": config.TENCENT_MEETING.get("operator_id_type", 1),
            "instanceid": 1,
            "to_operator_id": participant_id,
            "to_operator_id_type": 4,
        }
        return self._request(
            "POST",
            f"/v1/meetings/{meeting_id}/waiting-room/admit",
            body,
            action="admit_waiting_room",
        )

    def list_participants(self, meeting_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/meetings/{meeting_id}/participants?userid={config.TENCENT_MEETING.get('operator_id', '')}&instanceid=1",
            action="list_participants",
        )

    # ── 云录制 ────────────────────────────────────────────────────────────────

    def start_cloud_recording(self, meeting_id: str) -> Dict[str, Any]:
        body = {
            "userid": config.TENCENT_MEETING.get("operator_id", ""),
            "instanceid": 1,
            "record_type": 0,
        }
        return self._request(
            "POST",
            f"/v1/meetings/{meeting_id}/record",
            body,
            action="start_cloud_recording",
        )

    def stop_cloud_recording(self, meeting_id: str) -> Dict[str, Any]:
        body = {
            "userid": config.TENCENT_MEETING.get("operator_id", ""),
            "instanceid": 1,
        }
        return self._request(
            "POST",
            f"/v1/meetings/{meeting_id}/record/stop",
            body,
            action="stop_cloud_recording",
        )

    def get_recording_list(self, meeting_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/meetings/{meeting_id}/recordings",
            action="get_recording_list",
        )

    def kick_unauthorized(
        self,
        meeting_id: str,
        allowed_names: List[str],
    ) -> List[Dict[str, Any]]:
        """批量踢出不在白名单中的参会者"""
        result = self.list_participants(meeting_id)
        kicked = []
        if not result.get("success"):
            return kicked

        participants = result.get("data", {}).get("participants", [])
        allowed_lower = {n.lower() for n in allowed_names}
        for p in participants:
            name = p.get("user_name", p.get("nick_name", ""))
            pid = p.get("userid", p.get("uuid", ""))
            if name.lower() not in allowed_lower and pid:
                kick_result = self.remove_participant(meeting_id, pid, name)
                kicked.append({"name": name, "id": pid, "result": kick_result})
        return kicked
