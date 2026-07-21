from __future__ import annotations

import logging
from pathlib import Path

from telegram import Bot

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    async def send_alert(
        self,
        camera_ip: str,
        event_type: str,
        clip_path: Path | str | None = None,
    ) -> None:
        text = (
            f"🚨 Alerta de Monitoramento\n\n"
            f"Câmera: {camera_ip}\n"
            f"Evento: {event_type}\n"
            f"Horário: {self._now()}"
        )

        if clip_path:
            clip_path = Path(clip_path)
            if clip_path.exists():
                with open(clip_path, "rb") as video:
                    await self.bot.send_video(
                        chat_id=self.chat_id,
                        video=video,
                        caption=text,
                    )
                logger.info("Telegram alert sent with video to %s", self.chat_id)
                return

        await self.bot.send_message(chat_id=self.chat_id, text=text)
        logger.info("Telegram alert sent to %s", self.chat_id)

    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
