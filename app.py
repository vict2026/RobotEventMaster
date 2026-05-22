"""
RobotEventMaster — Streamlit 主入口
智能机器人赛事全流程管理智能体
"""
import streamlit as st

import config
from database.db import init_db
from services.scheduler import EventScheduler
from services.tencent_meeting import TencentMeetingClient
from services.voice_tts import VoiceService
from services.scoring_agent import ScoringAgent
from ui.components import render_sidebar_status
from ui.pages.monitor import render_monitor
from ui.pages.scoring import render_scoring
from ui.pages.review import render_review
from ui.pages.templates import render_templates
from ui.pages.map_upload import render_map_upload

st.set_page_config(
    page_title="RobotEventMaster",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def bootstrap():
    init_db()
    meeting = TencentMeetingClient()
    voice = VoiceService()
    scoring = ScoringAgent()
    scheduler = EventScheduler(
        meeting_client=meeting,
        voice_service=voice,
        scoring_agent=scoring,
    )
    return scheduler, meeting, voice, scoring


def main():
    scheduler, meeting, voice, scoring = bootstrap()

    st.sidebar.title("RobotEventMaster")
    st.sidebar.markdown("智能机器人赛事管理")
    render_sidebar_status(scheduler.state)

    pages = {
        "实时监控": render_monitor,
        "自动评分": render_scoring,
        "视频复核": render_review,
        "话术模板": render_templates,
        "地图上传": render_map_upload,
    }

    selection = st.sidebar.radio("导航", list(pages.keys()))
    st.sidebar.divider()
    st.sidebar.caption(f"赛事: {config.EVENT_DEFAULTS['event_name']}")
    st.sidebar.caption(f"数据库: {config.DATABASE_URL.split('/')[-1]}")

    page_fn = pages[selection]
    if selection in ("话术模板",):
        page_fn(voice)
    elif selection in ("自动评分", "视频复核", "地图上传"):
        page_fn(scoring)
    else:
        page_fn(scheduler)


if __name__ == "__main__":
    main()
