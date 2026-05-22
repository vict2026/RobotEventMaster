"""
Edge-TTS 语音提示服务
支持 config.py 中的自定义话术模板渲染与播放
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import config
from database.db import write_audit_log

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, tts_config: Optional[Dict[str, str]] = None):
        self.config = tts_config or config.TTS_CONFIG
        self.templates = dict(config.SPEECH_TEMPLATES)
        self.audio_dir = config.AUDIO_DIR

    def render_template(self, template_key: str, **kwargs) -> str:
        """渲染话术模板，合并 EVENT_DEFAULTS 占位符"""
        if template_key not in self.templates:
            raise KeyError(f"Unknown template: {template_key}")
        merged = {**config.EVENT_DEFAULTS, **kwargs}
        try:
            return self.templates[template_key].format(**merged)
        except KeyError as exc:
            logger.warning("Missing template key %s, using raw template", exc)
            return self.templates[template_key]

    async def _synthesize_async(self, text: str, output_path: Path) -> Path:
        import edge_tts

        communicate = edge_tts.Communicate(
            text,
            voice=self.config["voice"],
            rate=self.config["rate"],
            volume=self.config["volume"],
        )
        await communicate.save(str(output_path))
        return output_path

    def synthesize(self, text: str, filename: Optional[str] = None) -> Path:
        """将文本合成为 MP3 文件"""
        fname = filename or f"tts_{uuid.uuid4().hex[:8]}.mp3"
        output_path = self.audio_dir / fname
        asyncio.run(self._synthesize_async(text, output_path))
        write_audit_log(
            action="tts.synthesize",
            resource=str(output_path),
            detail={"text_length": len(text), "voice": self.config["voice"]},
        )
        return output_path

    def speak_template(self, template_key: str, **kwargs) -> Path:
        """渲染模板并合成语音"""
        text = self.render_template(template_key, **kwargs)
        safe_name = f"{template_key}_{uuid.uuid4().hex[:6]}.mp3"
        return self.synthesize(text, safe_name)

    def update_template(self, template_key: str, content: str):
        """运行时更新话术模板（同时写回 config 模块）"""
        self.templates[template_key] = content
        config.SPEECH_TEMPLATES[template_key] = content
        write_audit_log(
            action="tts.update_template",
            resource=template_key,
            detail={"length": len(content)},
        )

    def get_all_templates(self) -> Dict[str, str]:
        return dict(self.templates)

    def list_voices(self) -> list:
        """列出可用中文语音"""
        async def _list():
            import edge_tts
            voices = await edge_tts.list_voices()
            return [v for v in voices if v["Locale"].startswith("zh-")]

        return asyncio.run(_list())
