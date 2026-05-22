"""赛后视频复核页面"""
import streamlit as st
from pathlib import Path

import config


def render_review(scoring_agent):
    st.header("赛后视频复核")

    uploaded = st.file_uploader(
        "上传比赛录像",
        type=["mp4", "avi", "mov", "mkv"],
        key="review_video",
    )
    team_name = st.text_input("队伍名称", value="Team-A", key="review_team")
    segment_id = st.selectbox(
        "赛段",
        [s["id"] for s in config.EVENT_SEGMENTS],
        format_func=lambda x: next(s["name"] for s in config.EVENT_SEGMENTS if s["id"] == x),
        key="review_segment",
    )
    sample_interval = st.slider("帧采样间隔", 1, 30, config.SCORING_CONFIG["frame_sample_interval"], key="review_interval")

    if uploaded and st.button("开始复核评分", key="start_review"):
        save_path = config.ASSETS_DIR / "videos" / uploaded.name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(uploaded.read())

        with st.spinner("正在分析视频，请稍候..."):
            try:
                result = scoring_agent.score_video(
                    str(save_path),
                    team_name,
                    segment_id,
                    sample_interval,
                )
                st.success("复核完成")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("总分", result.total_score)
                c2.metric("任务完成", f"{result.task_completion}%")
                c3.metric("准确度", f"{result.accuracy}%")
                c4.metric("时间加分", result.time_bonus)
                c5.metric("罚分", result.penalty)

                if result.roi_hits:
                    st.subheader("ROI 命中统计")
                    st.bar_chart(result.roi_hits)

                st.subheader("检测明细（前50条）")
                st.dataframe(
                    [d.to_dict() for d in result.detections[:50]],
                    use_container_width=True,
                    hide_index=True,
                )
            except Exception as exc:
                st.error(f"分析失败: {exc}")

    st.divider()
    st.subheader("人工复核")
    history = scoring_agent.get_score_history(20)
    unreviewed = [h for h in history if not h.get("reviewed")]

    if unreviewed:
        selected = st.selectbox(
            "选择待复核记录",
            unreviewed,
            format_func=lambda x: f"#{x['id']} {x['team_name']} — {x['total_score']}分",
            key="review_select",
        )
        reviewer = st.text_input("复核人", key="reviewer_name")
        notes = st.text_area("复核备注", key="review_notes")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("通过", key="approve_review"):
                scoring_agent.update_review(selected["id"], reviewer, notes, approved=True)
                st.success("已通过")
                st.rerun()
        with c2:
            if st.button("驳回", key="reject_review"):
                scoring_agent.update_review(selected["id"], reviewer, notes, approved=False)
                st.warning("已驳回")
                st.rerun()
    else:
        st.info("暂无待复核记录")
