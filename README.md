# RobotEventMaster

智能机器人赛事全流程管理 Streamlit 智能体，集成腾讯会议企业版 API、Edge-TTS 语音提示、APScheduler 定时调度、YOLOv11 CV 自动评分。

## 功能

| 模块 | 说明 |
|------|------|
| 定时调度 | APScheduler 自动创建会议、播放话术、赛段切换、踢出未授权参会者 |
| 腾讯会议 | CreateMeeting / 云录制 / RemoveParticipant / MoveWaitingRoom |
| 语音提示 | Edge-TTS + config.py 自定义话术模板（含完整开场白） |
| CV 评分 | scoring_agent.py — YOLOv11 检测 + 高清地图 ROI |
| Streamlit UI | 实时监控、自动评分、视频复核、话术编辑、地图上传 |
| 审计日志 | PostgreSQL / SQLite 全量记录 |

## 项目结构

```
RobotEventMaster/
├── app.py                  # Streamlit 主入口
├── config.py               # 全局配置与话术模板
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── api/
│   └── signature.py        # 腾讯会议 HMAC 签名
├── database/
│   ├── db.py               # 数据库连接
│   └── models.py           # ORM 模型
├── services/
│   ├── scheduler.py        # APScheduler 调度
│   ├── tencent_meeting.py  # 腾讯会议 API
│   ├── voice_tts.py        # Edge-TTS
│   └── scoring_agent.py    # CV 评分
├── ui/
│   ├── components.py
│   └── pages/              # 各功能页面
└── assets/
    ├── maps/               # 赛场地图 & ROI
    └── audio/              # TTS 音频缓存
```

## 快速开始

### 本地运行（SQLite）

```bash
pip install -r requirements.txt
cp .env.example .env   # 编辑腾讯会议 API 密钥
streamlit run app.py
```

### Docker（PostgreSQL）

```bash
cp .env.example .env
docker compose up -d
# 访问 http://localhost:8501
```

## 配置

1. 复制 `.env.example` 为 `.env`，填入腾讯会议企业版凭证
2. `config.py` 中 `SPEECH_TEMPLATES["welcome"]` 已固定完整开场白
3. 可选：下载 YOLOv11 权重到 `models/yolov11n.pt`（无模型时使用 mock 检测）

## 腾讯会议 API

所有请求通过 `api/signature.py` 生成 HMAC-SHA256 签名，客户端封装在 `services/tencent_meeting.py`。

## 许可证

MIT
