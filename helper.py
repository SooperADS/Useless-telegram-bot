from collections.abc import Awaitable
from typing import Any, Callable
from copy import Error

import re as regex
import random

from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, ChatPermissions, Message
from aiogram import Bot
from aiogram.enums import ChatType

from config import * 

def contains_bad_words(text: str | None) -> bool:
	if not text:
		return False

	cleaned_text = regex.sub(r'[^\w\s]', '', text.lower())
	for word in cleaned_text.split():
		if word in BAD_WORDS:
			return True

	return False

async def is_admin(chat_id: int, user_id: int, bot: Bot) -> bool:
	try:
		member = await bot.get_chat_member(chat_id, user_id)
		return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
	except Exception:
		return False

def get_ping_message():
	return random.choice(PING_MESSAGES)

type UserActionCallback = Callable[[Bot, int, int], Awaitable[Any]] # pyright: ignore[reportExplicitAny]

class UserAction:
	callback: UserActionCallback
	bot_target_err_msg: str
	no_target_err_msg: str
	err_exception_msg: str
	success_msg: str

	def __init__(
		self,
		callback: UserActionCallback,
		no_target_err_msg: str,
		bot_target_err_msg: str,
		err_exception_msg: str,
		success_msg: str
	):
		self.callback = callback
		self.bot_target_err_msg = bot_target_err_msg
		self.no_target_err_msg = no_target_err_msg
		self.err_exception_msg = err_exception_msg
		self.success_msg = success_msg

	async def run_action(self, message: Message, bot: Bot) -> Any: # pyright: ignore[reportExplicitAny, reportAny]
		if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
			return await message.answer("Эта команда работает только в группах.")
		
		# Тест на идиота 🤡
		if message.from_user == None:
			raise Error("API кал; оно сломалось")
			
		if not await is_admin(message.chat.id, message.from_user.id, bot):
			return await message.answer("Вы не являетесь администратором этой группы.")

		if message.reply_to_message == None:
			return await message.answer(self.no_target_err_msg)

		target_user = message.reply_to_message.from_user
		if target_user == None:
			return await message.answer("Это команда не работает с системгыми сообщеними.")

		target_id = target_user.id

		if target_id == bot.id:
			return await message.answer(self.bot_target_err_msg)

		try:
			await self.callback(bot, message.chat.id, target_id)
			_ = await message.answer(self.success_msg.format(target_user.full_name))  
			return await message.delete()
		except Exception as e:
			return await message.answer(self.err_exception_msg.format(e))

BAN_ACTION = UserAction(
	lambda bot, chat_id, user_id: bot.ban_chat_member(chat_id, user_id),
	no_target_err_msg="Пожалуйста, ответьте на сообщение пользователя, которого хотите забанить.",
	bot_target_err_msg="Нельзя забанить бота.",
	success_msg="Пользователь {} забанен.",
	err_exception_msg="Ошибка при бане: {}"
)

MUTE_ACTION = UserAction(
	lambda bot, chat_id, user_id: bot.restrict_chat_member(
		chat_id,
		user_id,
		permissions=ChatPermissions(can_send_messages=False)
	),
	no_target_err_msg="Пожалуйста, ответьте на сообщение пользователя, которого хотите замутить.",
	bot_target_err_msg="Нельзя замутить бота.",
	success_msg="Пользователь {} замучен (не может писать).",
	err_exception_msg="Ошибка при муте: {}"
)
