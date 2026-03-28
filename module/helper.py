from aiogram.types import Chat, ChatMemberAdministrator, ChatMemberOwner, Message
from aiogram.enums import ChatType
from aiogram import Bot

from typing import Any, Callable
from datetime import datetime

import random
import logging
import sys
import os

from .config import * 

async def is_admin(chat_id: int, user_id: int, bot: Bot) -> bool:
	try:
		return isinstance(
			await bot.get_chat_member(chat_id, user_id),
			(ChatMemberAdministrator, ChatMemberOwner)
		)
	except Exception: return False

def get_ping_message() -> str:
	return random.choice(PING_MESSAGES)

def bot_in_supported_chat(chat: Chat) -> bool:
	return chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]

def is_service_message(message: Message) -> bool:
	return (
		message.text or
		message.audio or
		message.animation or
		message.document or
		message.game or
		message.photo or
		message.sticker or
		message.video or
		message.video_note or
		message.voice or
		message.checklist or
		message.contact or
		message.venue or
		message.location or
		message.paid_media or
		message.passport_data or
		message.poll or
		message.dice or
		message.giveaway or
		message.story or
		None
	) == None

def log_err(error: Exception):
	logging.exception(error)

def safe_result[R](fx: Callable[..., R], *pos: Any, **args: Any) -> R | None:
	try: 
		return fx(pos, **args)
	except Exception as error:
		log_err(error)

def test_funny_event_chance(ratio: int = 10) -> bool:
	return random.randint(0, 100 * ratio) / ratio < (FUNNY_EVENT_CHANCE - 1)

def setup_logger():
	if not os.path.exists("./logs"):
		os.makedirs("./logs")

	o = datetime.now()

	logging.basicConfig(
		level=logging.INFO,
		filename=f"./logs/{o.day}-{o.month}-{o.year} {o.hour}-{o.minute}-{o.second}.log",
		filemode="w+"
	)
	logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
