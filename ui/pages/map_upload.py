"""地图上传与 ROI 标注"""
import json
import streamlit as st
from PIL import Image, ImageDraw

import config


def render_map_upload(scoring_agent):
    st.header("地图上传")
    st.caption("上传高清赛场地图，配置 ROI 评分区域")

    uploaded = st.file_uploader("上传地图", type=["png", "jpg", "jpeg", "webp"], key="map_upload")

    if uploaded:
        save_path = config.MAPS_DIR / uploaded.name
        save_path.write_bytes(uploaded.read())
        scoring_agent.roi_config.map_path = str(save_path)
        scoring_agent.roi_config.save_to_json()
        st.success(f"地图已保存: {save_path.name}")

    roi = scoring_agent.roi_config
    if roi.map_path:
        st.subheader("当前地图")
        img = Image.open(roi.map_path)
        draw = ImageDraw.Draw(img)
        colors = {
            "task": "#00FF00",
            "penalty": "#FF0000",
            "bonus": "#FFD700",
            "start": "#00BFFF",
            "finish": "#FF69B4",
        }
        for zone in roi.zones:
            color = colors.get(zone.zone_type, "#FFFFFF")
            draw.rectangle(
                [zone.x, zone.y, zone.x + zone.width, zone.y + zone.height],
                outline=color,
                width=3,
            )
            draw.text((zone.x + 4, zone.y + 4), zone.name, fill=color)
        st.image(img, caption=roi.map_path, use_container_width=True)

    st.subheader("交互式 ROI 标注")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("区域名称", key="map_roi_name")
        zone_type = st.selectbox(
            "区域类型",
            ["task", "penalty", "bonus", "start", "finish"],
            key="map_roi_type",
        )
    with c2:
        points = st.number_input("分值", 0, 100, 10, key="map_roi_points")

    c3, c4, c5, c6 = st.columns(4)
    rx = c3.number_input("X 坐标", 0, 10000, 0, key="map_roi_x")
    ry = c4.number_input("Y 坐标", 0, 10000, 0, key="map_roi_y")
    rw = c5.number_input("宽度", 1, 10000, 200, key="map_roi_w")
    rh = c6.number_input("高度", 1, 10000, 200, key="map_roi_h")

    if st.button("添加 ROI 并保存", key="map_add_roi"):
        from services.scoring_agent import ROIZone
        roi.add_zone(ROIZone(name, rx, ry, rw, rh, zone_type, points))
        st.success(f"ROI '{name}' 已保存")
        st.rerun()

    if roi.zones and st.button("清除所有 ROI", key="clear_roi"):
        roi.zones = []
        roi.save_to_json()
        st.warning("已清除")
        st.rerun()

    st.subheader("ROI 配置 JSON")
    roi_file = config.MAPS_DIR / "roi_config.json"
    if roi_file.exists():
        st.code(roi_file.read_text(encoding="utf-8"), language="json")

    st.download_button(
        "导出 ROI 配置",
        data=json.dumps(
            {"map_path": roi.map_path, "zones": [z.to_dict() for z in roi.zones]},
            ensure_ascii=False,
            indent=2,
        ),
        file_name="roi_config.json",
        mime="application/json",
    )
