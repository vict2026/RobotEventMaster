import json
from pathlib import Path

# ================== 腾讯会议企业版配置 ==================
TENCENT_MEETING = {
    "secret_id": "你的SecretId",
    "secret_key": "你的SecretKey",
    "appid": "你的AppID",
    "app_id": "你的AppID",
    "sdk_id": "",
    "host_userid": "主持人企业用户ID",
    "base_url": "https://api.meeting.qq.com",
}

# ================== TTS语音配置 ==================
TTS_CONFIG = {
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "+0%",
    "volume": "+0%"
}

# ================== 话术模板 ==================
TTS_TEMPLATES = {
    "welcome": "请参赛同学请注意，比赛即将开始。请确认摄像头、麦克风状态正常，并保持比赛区域清晰可见。倒计时结束后，系统将自动进入比赛倒计时，请在5分钟内完成自我介绍与比赛任务，5分钟结束后请自动离场。请听到开始提示后再进行操作。三、二、一，比赛开始。",
    "start_auto": "自动任务阶段开始，240秒倒计时开始。",
    "modify": "自动任务结束，进入1分钟设备改造时间。",
    "start_manual": "手动任务阶段开始。",
    "time_remain_30": "剩余30秒，请准备返回出发区。",
    "end": "比赛结束！请立即停止机器人。",
    "next_group": "下一组选手准备，10秒后开始。",
}

SPEECH_TEMPLATES = TTS_TEMPLATES

# ================== 数据库配置 ==================
import os
import sys
from pathlib import Path

# ==================== 动态数据库路径（关键修复） ====================
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的可执行文件所在目录
    base_path = Path(sys.executable).parent
else:
    # 开发模式：config.py 所在目录
    base_path = Path(__file__).parent

data_dir = base_path / "data"
data_dir.mkdir(exist_ok=True)   # 自动确保 data 文件夹存在

DATABASE_URL = f"sqlite:///{data_dir / 'competition.db'}"
# ============================================================

# ================== 音频目录 ==================
AUDIO_DIR = "data/audio"

# ================== 地图目录 ==================
MAPS_DIR = Path("data")

# ================== 评分配置（已包含所有已知字段） ==================
SCORING_CONFIG = {
    "yolo_model_path": "models/yolov11n.pt",
    "confidence_threshold": 0.6,
    "iou_threshold": 0.5,
    "frame_sample_interval": 5,        # ← 新增：视频复核页面需要的帧采样间隔
    "score_weights": {
        "accuracy": 0.6,
        "consistency": 0.2,
        "timing": 0.2
    },
    "map_path": "data/high_res_map.png"
}

# ================== 调度器配置 ==================
SCHEDULER_CONFIG = {
    "daemon": False,
    "timezone": "Asia/Shanghai",
    "misfire_grace_time": 60
}

# ================== 事件默认配置 ==================
EVENT_DEFAULTS = {
    "event_name": "机器人比赛",
    "duration": 240,
    "auto_task_time": 240,
    "modify_time": 60,
    "manual_task_time": 300,
    "start_delay": 5
}

# ================== 视频复核页面需要的字段 ==================
EVENT_SEGMENTS = [
    {"id": "auto", "name": "自动任务阶段", "duration": 240},
    {"id": "modify", "name": "设备改造时间", "duration": 60},
    {"id": "manual", "name": "手动任务阶段", "duration": 300},
]

# ================== 模板保存/加载函数 ==================
def save_templates(templates: dict):
    Path("data/templates.json").write_text(json.dumps(templates, ensure_ascii=False, indent=2))

def load_templates():
    path = Path("data/templates.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return TTS_TEMPLATES