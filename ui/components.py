"""Streamlit 共享 UI 组件"""
import streamlit as st


def render_sidebar_status(scheduler_state: dict):
    st.sidebar.markdown("### 系统状态")
    running = scheduler_state.get("running", False)
    st.sidebar.metric("调度器", "运行中" if running else "已停止")
    st.sidebar.metric("当前赛段", scheduler_state.get("current_segment") or "—")
    st.sidebar.metric("会议 ID", scheduler_state.get("meeting_id") or "—")
    st.sidebar.metric("会议号", scheduler_state.get("meeting_code") or "—")


def render_audit_table(logs: list):
    if not logs:
        st.info("暂无审计日志")
        return
    import pandas as pd
    df = pd.DataFrame(logs)
    cols = [c for c in ["timestamp", "actor", "action", "resource"] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)
