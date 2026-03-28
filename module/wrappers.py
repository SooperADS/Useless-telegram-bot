from collections.abc import Awaitable
from aiogram.types import Message, User
from typing import Any, Callable

import logging
import functools

from .helper import *

"""
Декораторы. Вы любите декораторы в Python? Я ИХ ОБОЖАЮ (нет)
"""

async def __on_validation_err(message: Message, text: str| None):
	if isinstance(text, str):
		await message.reply(text)

type PipelineDecorator[
	InFx: Callable[..., Any],
	OutFx: Callable[..., Any] = InFx
] = Callable[[InFx], OutFx]

type Wrapper = Callable[..., Awaitable[Any]]

def safe(fx: Wrapper) -> Wrapper:
	async def __wrapper(*pos: Any):
		try:
			await fx(*pos)
		except Exception as error:
			log_err(error)
	return __wrapper

def discard_service_messages(fx: MainWrapper) -> MainWrapper:
	async def __wrapper(message: Message):
		if not is_service_message(message):
			await fx(message)
	
	return __wrapper

type MainWrapper = Callable[[Message], Awaitable[Any]]

def __validate_chat_type(
	fx: MainWrapper, /,
	fallback_message: str | None
) -> MainWrapper:
	async def __wrapper(message: Message):
		if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
			await fx(message)
		else: await __on_validation_err(message, fallback_message)
	
	return __wrapper

type BotWrapper = Callable[[Message, Bot], Awaitable[Any]]

def __bind_bot(
	fx: BotWrapper, /,
	bot: Bot
) -> MainWrapper:
	async def __wrapper(message: Message):
		await fx(message, bot)
	return __wrapper

def __validate_exec_is_admin(
	fx: BotWrapper, /,
	fallback_message: str | None
) -> BotWrapper:
	async def __wrapper(message: Message, bot: Bot):
		if message.from_user:
			if await is_admin(message.chat.id, message.from_user.id, bot):
				await fx(message, bot)
			else: await __on_validation_err(message, fallback_message)
		else: logging.warning("Получено сообщение без отправителя")
	return __wrapper

def unpack_user(fx: BotUserWrapper) -> BotWrapper:
	async def __wrapper(message: Message, bot: Bot):
		if message.from_user:
			await fx(message, bot, message.from_user)
		else: logging.warning("Получено сообщение без отправителя")
	return __wrapper

type BotUserWrapper = Callable[[Message, Bot, User], Awaitable[Any]]

def __unpack_target_as_replier(
	fx: BotUserWrapper, /,
	no_reply_fallback_message: str | None,
	no_target_fallback_message: str | None
) -> BotWrapper:
	async def __wrapper(message: Message, bot: Bot):
		if message.reply_to_message:
			user = message.reply_to_message.from_user
			if user:
				await fx(message, bot, user)
			else: await __on_validation_err(message, no_target_fallback_message)
		else: await __on_validation_err(message, no_reply_fallback_message)
	return __wrapper
	
def __validate_bot_is_not_target(
	fx: BotUserWrapper, /,
	fallback_message: str | None
) -> BotUserWrapper:
	async def __wrapper(message: Message, bot: Bot, user: User):
		if bot.id != user.id:
			await fx(message, bot, user)
		else: await __on_validation_err(message, fallback_message)
	return __wrapper
	
def __validate_target_not_bot(
	fx: BotUserWrapper, /,
	fallback_message: str | None
) -> BotUserWrapper:
	async def __wrapper(message: Message, bot: Bot, user: User):
		if not user.is_bot:
			await fx(message, bot, user)
		else: await __on_validation_err(message, fallback_message)
	return __wrapper
	
def __safe_on_command_action(
	fx: BotUserWrapper, /,
	success_message: str | None,
	on_exception_message: str | None,
) -> BotUserWrapper:
	async def __wrapper(message: Message, bot: Bot, user: User):
		try:
			await fx(message, bot, user)
			if isinstance(success_message, str):
				await message.answer(success_message.format(
					username=user.full_name
				))	
		except Exception as error:
			if isinstance(on_exception_message, str):
				await message.answer(on_exception_message.format(
					error=error
				))
			log_err(error)
		
		return await message.delete()
	return __wrapper

VEFM_INVALID_CHAT = "Эта команда работает только в группах."
def validate_chat_type(
	fallback_message: str | None = VEFM_INVALID_CHAT
) -> PipelineDecorator[MainWrapper]:
	return functools.partial(__validate_chat_type, fallback_message=fallback_message)

def bind_bot(bot: Bot) -> PipelineDecorator[BotWrapper, MainWrapper]:
	return functools.partial(__bind_bot, bot=bot)

VEFM_EXEC_NOT_ADMIN = "Для выполнения этой команды Вы должны быть администратором группы."
def validate_exec_is_admin(
	fallback_message: str | None = VEFM_EXEC_NOT_ADMIN
) -> PipelineDecorator[BotWrapper]:
	return functools.partial(__validate_exec_is_admin, fallback_message=fallback_message)

VEFM_NO_REPLY = "Для выполнения данной команды, ответьте на сообщение пользователя, для которого хотите выполнить команду."
VEFM_NO_REPLY_TARGET = "Цель не найдена."
def unpack_target_as_replier(
	no_reply_fallback_message: str | None = VEFM_NO_REPLY,
	no_target_fallback_message: str | None = VEFM_NO_REPLY_TARGET
) -> PipelineDecorator[BotUserWrapper, BotWrapper]:
	return functools.partial(
		__unpack_target_as_replier,
		no_reply_fallback_message=no_reply_fallback_message,
		no_target_fallback_message=no_target_fallback_message
	)

VEFM_CURRENT_BOT_IS_TARGET = "Я не могу быть целью данной команды 😉."
def validate_bot_not_target(
	fallback_message: str | None = VEFM_CURRENT_BOT_IS_TARGET
) -> PipelineDecorator[BotUserWrapper]:
	return functools.partial(__validate_bot_is_not_target, fallback_message=fallback_message)

VEFM_BOT_IS_TARGET = "Бот не может быть целью данной команды."
def validate_target_not_bot(
	fallback_message: str | None = VEFM_BOT_IS_TARGET
) -> PipelineDecorator[BotUserWrapper]:
	return functools.partial(__validate_target_not_bot, fallback_message=fallback_message)

VEFM_SUCCESS = "Команда выполнена успешно для пользователя **{username}**."
VEFM_CATCH_EXCEPTION = "Ошибка при выполнении команды. \n{error}"
def safe_on_command_action(
	success_message: str | None = VEFM_SUCCESS,
	on_exception_message: str | None = VEFM_CATCH_EXCEPTION,
) -> PipelineDecorator[BotUserWrapper]:
	return functools.partial(
		__safe_on_command_action,
		success_message=success_message,
		on_exception_message=on_exception_message
	)
