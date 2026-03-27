from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message, User
from datetime import datetime

from .module import wrappers
from .module import helper
from .module import censor
from .private import BOT_TOKEN

import asyncio
import logging

logging.basicConfig(level=logging.INFO, filename=f"./logs/{datetime.now()}.log", filemode="w+")

BOT = Bot(token=BOT_TOKEN)
DISPATCHER = Dispatcher()

GREETING_MESSAGE = """
Привет! Я бот-модератор.
Используйте /ban (в ответ на сообщение) для бана, /mute (в ответ на сообщение) для мута.
"""

# /start
@DISPATCHER.message(Command("start"))
@wrappers.safe
async def on_start_command(message: Message):
	return await message.answer(GREETING_MESSAGE)

# /ban
@DISPATCHER.message(Command("ban"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.validate_bot_not_target()
@wrappers.safe_action()
async def on_ban_command(message: Message, bot: Bot, user: User):
	await bot.ban_chat_member(message.chat.id, user.id)

# /unban
@DISPATCHER.message(Command("unban"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.safe_action()
async def on_unban_command(message: Message, bot: Bot, user: User):
	await bot.unban_chat_member(message.chat.id, user.id)
	await asyncio.sleep(10)
	await message.answer("Debug message! Must be sended with 10s delay after receiving command")

# /mute
@DISPATCHER.message(Command("mute"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.validate_bot_not_target()
@wrappers.safe_action()
async def on_mute_command(message: Message, bot: Bot, user: User):
	await bot.restrict_chat_member(
		message.chat.id,
		user.id,
		permissions=ChatPermissions(can_send_messages=False)
	)

# /unmute
@DISPATCHER.message(Command("unmute"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.validate_bot_not_target()
@wrappers.safe_action()
async def on_unmute_command(message: Message, bot: Bot, user: User):
	await bot.restrict_chat_member(
		message.chat.id,
		user.id,
		permissions=ChatPermissions(can_send_messages=True)
	)

# /ping
@DISPATCHER.message(Command("ping"))
@wrappers.safe
async def on_ping_command(message: Message):
	return await message.reply(text=helper.get_ping_message())

# /debug
@DISPATCHER.message(Command("debug"))
@wrappers.safe
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.safe_action()
async def on_debug_command(message: Message, bot: Bot, user: User):
	msg_dict = {
		"user_id": user.id,
		"has_reply_message": message.reply_to_message != None,
		"you_is_admin": helper.safe_result(
			helper.is_admin, message.chat.id, user.id, bot
		)
	}

	if message.reply_to_message:
		msg_dict["reply_target_is_service_message"] = helper.is_service_message(
			message.reply_to_message
		)

	return await message.answer(f"Debug information (for devs. only)\n\n{msg_dict}")

@DISPATCHER.message()
@wrappers.safe
@wrappers.validate_chat_type(None)
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.validate_bot_not_target(None)
async def dispatch_message(message: Message, _bot: Bot, _user: User):
	if not await censor.process_message(message) and helper.test_funny_event_chance():
		logging.info("Весёлое событие в ответ на сообщение")
		await message.reply(helper.get_ping_message())

async def main():
	await DISPATCHER.start_polling(BOT)

if __name__== "__main__" :
	asyncio.run(main())