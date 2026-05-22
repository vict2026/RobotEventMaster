"""
APScheduler 定时任务调度器
自动: 开启腾讯会议、语音提示、踢人、赛段切换
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

import config
from database.db import get_session, write_audit_log
from database.models import EventRecord

logger = logging.getLogger(__name__)


class EventScheduler:
    """赛事全流程定时调度"""

    def __init__(
        self,
        meeting_client=None,
        voice_service=None,
        scoring_agent=None,
    ):
        self.meeting = meeting_client
        self.voice = voice_service
        self.scoring = scoring_agent
        self.scheduler = BackgroundScheduler(**config.SCHEDULER_CONFIG)
        self._state: Dict[str, Any] = {
            "current_segment": None,
            "meeting_id": None,
            "meeting_code": None,
            "event_name": config.EVENT_DEFAULTS["event_name"],
            "running": False,
        }
        self._job_log: List[Dict] = []

    @property
    def state(self) -> Dict[str, Any]:
        return dict(self._state)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self._state["running"] = True
            write_audit_log(action="scheduler.start")
            logger.info("EventScheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self._state["running"] = False
            write_audit_log(action="scheduler.shutdown")

    def _log_job(self, job_id: str, status: str, detail: str = ""):
        entry = {
            "job_id": job_id,
            "status": status,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        self._job_log.append(entry)
        logger.info("Job [%s] %s: %s", job_id, status, detail)

    # ── 会议任务 ──────────────────────────────────────────────────────────────

    def schedule_create_meeting(
        self,
        run_at: datetime,
        subject: str,
        duration_min: int = 180,
    ) -> str:
        job_id = "create_meeting"

        def _task():
            if not self.meeting:
                self._log_job(job_id, "skipped", "meeting client not configured")
                return
            result = self.meeting.create_meeting(subject, duration_min=duration_min)
            if result.get("success"):
                data = result.get("data", {})
                meeting_info = data.get("meeting_info_list", [{}])[0]
                self._state["meeting_id"] = meeting_info.get("meeting_id", data.get("meeting_id"))
                self._state["meeting_code"] = meeting_info.get("meeting_code", "")
                self._log_job(job_id, "success", f"meeting_id={self._state['meeting_id']}")
            else:
                self._log_job(job_id, "failed", str(result))

        self.scheduler.add_job(
            _task,
            trigger=DateTrigger(run_date=run_at),
            id=job_id,
            replace_existing=True,
        )
        return job_id

    def schedule_start_recording(self, run_at: datetime) -> str:
        job_id = "start_recording"

        def _task():
            mid = self._state.get("meeting_id")
            if mid and self.meeting:
                result = self.meeting.start_cloud_recording(mid)
                self._log_job(job_id, "done", str(result.get("success")))

        self.scheduler.add_job(_task, DateTrigger(run_date=run_at), id=job_id, replace_existing=True)
        return job_id

    # ── 语音任务 ──────────────────────────────────────────────────────────────

    def schedule_voice(
        self,
        run_at: datetime,
        template_key: str,
        job_id: Optional[str] = None,
        **template_kwargs,
    ) -> str:
        jid = job_id or f"voice_{template_key}_{run_at.strftime('%H%M%S')}"

        def _task():
            if not self.voice:
                self._log_job(jid, "skipped", "voice service not configured")
                return
            try:
                audio_path = self.voice.speak_template(template_key, **template_kwargs)
                self._log_job(jid, "success", str(audio_path))
            except Exception as exc:
                self._log_job(jid, "failed", str(exc))

        self.scheduler.add_job(_task, DateTrigger(run_date=run_at), id=jid, replace_existing=True)
        return jid

    def schedule_welcome(self, run_at: datetime) -> str:
        return self.schedule_voice(
            run_at,
            "welcome",
            job_id="voice_welcome",
            event_name=self._state["event_name"],
        )

    # ── 赛段切换 ──────────────────────────────────────────────────────────────

    def schedule_segment_switch(
        self,
        segment: Dict[str, Any],
        start_at: datetime,
    ) -> str:
        seg_id = segment["id"]
        job_id = f"segment_{seg_id}"

        def _start_segment():
            self._state["current_segment"] = seg_id
            with get_session() as session:
                record = EventRecord(
                    event_name=self._state["event_name"],
                    segment_id=seg_id,
                    segment_name=segment["name"],
                    status="running",
                    started_at=datetime.utcnow(),
                )
                session.add(record)

            if self.voice:
                self.voice.speak_template(
                    "segment_start",
                    segment_name=segment["name"],
                    location=config.EVENT_DEFAULTS["location"],
                    countdown=segment.get("duration_min", 30),
                )
            write_audit_log(action="segment.start", resource=seg_id, detail=segment)
            self._log_job(job_id, "started", segment["name"])

        def _end_segment():
            if self.voice:
                self.voice.speak_template("segment_end", segment_name=segment["name"])
            with get_session() as session:
                rec = (
                    session.query(EventRecord)
                    .filter_by(segment_id=seg_id, status="running")
                    .order_by(EventRecord.id.desc())
                    .first()
                )
                if rec:
                    rec.status = "completed"
                    rec.ended_at = datetime.utcnow()
            write_audit_log(action="segment.end", resource=seg_id)
            self._log_job(f"{job_id}_end", "completed", segment["name"])

        end_at = start_at + timedelta(minutes=segment["duration_min"])

        self.scheduler.add_job(
            _start_segment,
            DateTrigger(run_date=start_at),
            id=job_id,
            replace_existing=True,
        )
        self.scheduler.add_job(
            _end_segment,
            DateTrigger(run_date=end_at),
            id=f"{job_id}_end",
            replace_existing=True,
        )
        return job_id

    def build_full_schedule(self, event_start: datetime):
        """根据 EVENT_SEGMENTS 构建完整赛程"""
        cursor = event_start
        for segment in config.EVENT_SEGMENTS:
            self.schedule_segment_switch(segment, cursor)
            cursor += timedelta(minutes=segment["duration_min"])

        self.schedule_welcome(event_start)
        self.schedule_create_meeting(event_start - timedelta(minutes=5), self._state["event_name"])
        self.schedule_start_recording(event_start + timedelta(minutes=1))
        write_audit_log(
            action="scheduler.build_full_schedule",
            detail={"start": event_start.isoformat(), "segments": len(config.EVENT_SEGMENTS)},
        )

    # ── 踢人任务 ──────────────────────────────────────────────────────────────

    def schedule_kick_unauthorized(
        self,
        interval_min: int,
        allowed_names: List[str],
    ) -> str:
        job_id = "kick_unauthorized"

        def _task():
            mid = self._state.get("meeting_id")
            if not mid or not self.meeting:
                return
            kicked = self.meeting.kick_unauthorized(mid, allowed_names)
            for k in kicked:
                if self.voice:
                    self.voice.speak_template(
                        "kick_done",
                        participant_name=k["name"],
                    )
            self._log_job(job_id, "done", f"kicked={len(kicked)}")

        self.scheduler.add_job(
            _task,
            trigger=IntervalTrigger(minutes=interval_min),
            id=job_id,
            replace_existing=True,
        )
        return job_id

    # ── 监控 ──────────────────────────────────────────────────────────────────

    def get_jobs(self) -> List[Dict]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def get_job_log(self, limit: int = 100) -> List[Dict]:
        return self._job_log[-limit:]

    def add_custom_job(
        self,
        func: Callable,
        trigger_type: str,
        job_id: str,
        **trigger_kwargs,
    ) -> str:
        triggers = {
            "date": DateTrigger,
            "interval": IntervalTrigger,
            "cron": CronTrigger,
        }
        trigger_cls = triggers.get(trigger_type, DateTrigger)
        self.scheduler.add_job(
            func,
            trigger=trigger_cls(**trigger_kwargs),
            id=job_id,
            replace_existing=True,
        )
        return job_id
