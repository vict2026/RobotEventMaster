"""自定义话术模板编辑"""
import streamlit as st

import config


def render_templates(voice_service):
    st.header("话术模板编辑")
    st.caption("修改后将立即生效，welcome 开场白为用户指定的完整模板")

    templates = voice_service.get_all_templates()
    template_keys = list(templates.keys())
    selected_key = st.selectbox("选择模板", template_keys, key="tpl_key")

    current = templates[selected_key]
    edited = st.text_area(
        f"编辑 — {selected_key}",
        value=current,
        height=300,
        key="tpl_content",
    )

    st.markdown("**可用占位符**")
    placeholders = {
        "welcome": ["{event_name}", "{organizer}", "{co_organizer}"],
        "segment_start": ["{segment_name}", "{location}", "{countdown}"],
        "segment_end": ["{segment_name}"],
        "kick_warning": ["{participant_name}", "{grace_seconds}"],
        "kick_done": ["{participant_name}"],
        "scoring_start": ["{team_name}"],
        "scoring_done": ["{team_name}", "{total_score}"],
        "break_reminder": ["{remaining_min}"],
        "emergency": ["{message}"],
    }
    st.code(", ".join(placeholders.get(selected_key, ["见 EVENT_DEFAULTS"])))

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("保存模板", key="save_tpl"):
            voice_service.update_template(selected_key, edited)
            st.success(f"模板 {selected_key} 已保存")
            st.rerun()
    with c2:
        if st.button("重置为默认", key="reset_tpl"):
            default = config.SPEECH_TEMPLATES.get(selected_key, current)
            voice_service.update_template(selected_key, default)
            st.info("已重置")
            st.rerun()
    with c3:
        if st.button("试听", key="preview_tpl"):
            with st.spinner("合成中..."):
                try:
                    merged = {**config.EVENT_DEFAULTS}
                    if selected_key == "segment_start":
                        merged.update({"segment_name": "测试赛段", "countdown": 5})
                    elif selected_key == "kick_done":
                        merged.update({"participant_name": "测试用户"})
                    audio_path = voice_service.speak_template(selected_key, **merged)
                    st.audio(str(audio_path))
                except Exception as exc:
                    st.error(f"合成失败: {exc}")

    if selected_key == "welcome":
        st.info("welcome 开场白为固定长模板，请谨慎修改。")

    st.divider()
    st.subheader("赛事默认参数")
    for key, val in config.EVENT_DEFAULTS.items():
        new_val = st.text_input(key, value=val, key=f"evt_{key}")
        config.EVENT_DEFAULTS[key] = new_val

    st.subheader("Edge-TTS 语音设置")
    voice = st.text_input("Voice", value=config.TTS_CONFIG["voice"], key="tts_voice")
    rate = st.text_input("Rate", value=config.TTS_CONFIG["rate"], key="tts_rate")
    if st.button("应用 TTS 设置", key="apply_tts"):
        config.TTS_CONFIG["voice"] = voice
        config.TTS_CONFIG["rate"] = rate
        voice_service.config = config.TTS_CONFIG
        st.success("TTS 设置已更新")
