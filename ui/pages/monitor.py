"""实时监控页面"""
import streamlit as st
from datetime import datetime, timedelta

import config
from database.db import get_session
from database.models import AuditLog, EventRecord, MeetingLog
from ui.components import render_audit_table


def render_monitor(scheduler):
    st.header("实时监控")
    col1, col2, col3, col4 = st.columns(4)
    state = scheduler.state

    with col1:
        st.metric("调度器状态", "运行中" if state.get("running") else "已停止")
    with col2:
        st.metric("当前赛段", state.get("current_segment") or "—")
    with col3:
        st.metric("会议 ID", (state.get("meeting_id") or "—")[:12])
    with col4:
        st.metric("赛事名称", state.get("event_name", "—"))

    st.subheader("调度任务")
    jobs = scheduler.get_jobs()
    if jobs:
        st.dataframe(jobs, use_container_width=True, hide_index=True)
    else:
        st.info("暂无已调度任务")

    st.subheader("任务执行日志")
    job_log = scheduler.get_job_log(50)
    if job_log:
        st.dataframe(job_log, use_container_width=True, hide_index=True)
    else:
        st.info("暂无执行记录")

    st.subheader("快捷操作")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("启动调度器", key="start_sched"):
            scheduler.start()
            st.success("调度器已启动")
            st.rerun()
    with c2:
        if st.button("停止调度器", key="stop_sched"):
            scheduler.shutdown()
            st.warning("调度器已停止")
            st.rerun()
    with c3:
        if st.button("构建完整赛程", key="build_sched"):
            start = datetime.now() + timedelta(minutes=2)
            scheduler.build_full_schedule(start)
            st.success(f"赛程已从 {start.strftime('%H:%M:%S')} 开始构建")
            st.rerun()

    st.divider()
    tab1, tab2, tab3 = st.tabs(["赛事记录", "会议日志", "审计日志"])

    with tab1:
        with get_session() as session:
            records = session.query(EventRecord).order_by(EventRecord.id.desc()).limit(30).all()
            st.dataframe([r.to_dict() for r in records], use_container_width=True, hide_index=True)

    with tab2:
        with get_session() as session:
            logs = session.query(MeetingLog).order_by(MeetingLog.id.desc()).limit(30).all()
            st.dataframe([l.to_dict() for l in logs], use_container_width=True, hide_index=True)

    with tab3:
        with get_session() as session:
            audits = session.query(AuditLog).order_by(AuditLog.id.desc()).limit(50).all()
            render_audit_table([a.to_dict() for a in audits])

    st.subheader("赛段时间表")
    st.dataframe(config.EVENT_SEGMENTS, use_container_width=True, hide_index=True)
