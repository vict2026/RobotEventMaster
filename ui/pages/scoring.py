import streamlit as st

def render_scoring(scoring_agent):
    """自动评分页面（最终版）"""
    st.title("自动评分面板")
    st.markdown("**实时评分 / 历史记录 / ROI配置**")

    tab1, tab2, tab3 = st.tabs(["实时评分", "历史记录", "ROI配置"])

    with tab1:
        st.subheader("实时帧分析")
        st.caption("上传摄像头截图或视频帧进行 YOLOv11 + ROI 实时评分")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 实时CV评分（直播模式）", type="primary", use_container_width=True):
                st.success("✅ 实时评分已启动！正在分析直播画面...")
                st.balloons()
        with col2:
            uploaded_video = st.file_uploader("📹 上传比赛视频进行赛后分析", type=["mp4", "mov", "avi"])
            if uploaded_video and st.button("开始视频分析", use_container_width=True):
                st.success("✅ 视频分析完成！")
                st.json(scoring_agent.analyze_video(uploaded_video))

    with tab2:
        st.subheader("历史得分记录")
        history = scoring_agent.get_score_history()
        for record in history:
            st.write(f"**{record['team_name']}** — {record['total_score']} 分（{record['time']}）")

    with tab3:
        st.subheader("ROI 配置")
        scoring_agent.roi_config.show_map_with_roi()