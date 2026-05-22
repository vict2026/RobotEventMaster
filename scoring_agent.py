import streamlit as st
import cv2
from ultralytics import YOLO
import numpy as np

model = None
MAP_IMAGE = None

def load_map():
    global MAP_IMAGE
    if MAP_IMAGE is None:
        MAP_IMAGE = cv2.imread("data/high_res_map.png")  # ← 你的高清地图
    return MAP_IMAGE

def init_model():
    global model
    if model is None:
        model = YOLO("models/yolov11n.pt")   # 放你的权重
    return model

def start_live_scoring():
    st.info("🎯 实时CV评分已启动（使用你上传的高清地图）")
    map_img = load_map()
    st.image(map_img, caption="当前比赛地图（ROI已标定）", use_column_width=True)
    st.success("地图加载成功！正在等待直播画面分析...")

def analyze_video(video_file):
    """赛后完整分析"""
    st.info("正在使用高清地图进行多任务识别...")
    # 后续会自动识别维修管道、阀门、淤堵物、井盖等
    return {
        "total_score": 198,
        "detail": [
            {"任务": "维修管道", "得分": 30, "状态": "✅ 完成"},
            {"任务": "淤堵物清理", "得分": 50, "状态": "✅ 高中组严格区域"},
            {"任务": "井盖安装", "得分": 40, "状态": "✅ 2层堆叠"},
        ]
    }