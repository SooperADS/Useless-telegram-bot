from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import KICKED, ChatMemberUpdatedFilter, Command
from aiogram.types import ChatMemberUpdated, ChatPermissions, Message, User

from module import wrappers
from module import helper
from module import censor
from private import BOT_TOKEN

import asyncio
import logging

#TODO:
#> Больше информации о боте
#> Команда help
#> Аргументы команд
#> unban -> pardon
#> debug -> debug user
#> Специальный сообщения для каждой команды

helper.setup_logger()

BOT = Bot(BOT_TOKEN,default=DefaultBotProperties(
	parse_mode=ParseMode.MARKDOWN
))
DISPATCHER = Dispatcher()

GREETING_MESSAGE = """
Привет! Я бот-модератор.
Используйте /ban (в ответ на сообщение) для бана, /mute (в ответ на сообщение) для мута.
"""

# /start
@DISPATCHER.message(Command("start"))
@wrappers.safe
async def on_start_command(message: Message):
	await message.answer(GREETING_MESSAGE)

# /ban
@DISPATCHER.message(Command("ban"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.validate_bot_not_target()
@wrappers.safe_on_command_action()
async def on_ban_command(message: Message, bot: Bot, user: User):
	await bot.ban_chat_member(message.chat.id, user.id)

# /unban
@DISPATCHER.message(Command("unban"))
@wrappers.safe
@wrappers.validate_chat_type()
@wrappers.bind_bot(BOT)
@wrappers.validate_exec_is_admin()
@wrappers.unpack_target_as_replier()
@wrappers.safe_on_command_action()
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
@wrappers.safe_on_command_action()
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
@wrappers.safe_on_command_action()
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
	await message.reply(text=helper.get_ping_message())

# /debug
@DISPATCHER.message(Command("debug"))
@wrappers.safe
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.safe_on_command_action()
async def on_debug_command(message: Message, bot: Bot, user: User):
	chat_id = message.chat.id
	msg_dict = {
		"`user_id`": user.id,
		"`chat_id`": chat_id,
		"`has_reply_message`": message.reply_to_message != None,
		"`you_is_admin`": helper.safe_result(
			helper.is_admin, chat_id, user.id, bot
		),
		"`chat_censor_enable`": censor.is_enable_in_chat(chat_id)
	}

	if message.reply_to_message:
		msg_dict["`reply_target_is_service_message`"] = helper.is_service_message(
			message.reply_to_message
		)

	await message.answer(f"Debug information (for devs. only)\n\n{msg_dict}")

# /censor-state
@DISPATCHER.message(Command("censor-state"))
@wrappers.safe
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.safe_on_command_action()
async def on_censor_state_command(message: Message, _bot: Bot, _user: User):
	msg_state: str = "**включена**"
	if censor.is_enable_in_chat(message.chat.id):
		msg_state = "**включено**"
	await message.answer(f"Модерация мата в чате: {msg_state}")

# /censor-on
@DISPATCHER.message(Command("censor-on"))
@wrappers.safe
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.safe_on_command_action()
async def on_censor_on_command(message: Message, _bot: Bot, _user: User):
	if censor.is_enable_in_chat(message.chat.id):
		await message.answer(f"Модерация мата в чате уже включена")
	else:
		censor.enable_in_chat(message.chat.id) 
		await message.answer(f"Включена модерация мата в чате")

# /censor-off
@DISPATCHER.message(Command("censor-off"))
@wrappers.safe
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.safe_on_command_action()
async def on_censor_off_command(message: Message, _bot: Bot, _user: User):
	if censor.is_enable_in_chat(message.chat.id):
		await message.answer(f"Модерация мата в чате уже выключена")
	else:
		censor.disable_in_chat(message.chat.id) 
		await message.answer(f"Выключена модерация мата в чате")

@DISPATCHER.message()
@wrappers.safe
@wrappers.validate_chat_type(None)
@wrappers.discard_service_messages
@wrappers.bind_bot(BOT)
@wrappers.unpack_user
@wrappers.validate_bot_not_target(None)
async def dispatch_message(message: Message, _bot: Bot, _user: User):
	if not await censor.process_message(message) and helper.test_funny_event_chance():
		logging.info("Весёлое событие в ответ на сообщение")
		await message.reply(helper.get_ping_message())

@DISPATCHER.my_chat_member(ChatMemberUpdatedFilter(KICKED))
@wrappers.safe
async def on_kick(event: ChatMemberUpdated):
	censor.forget_chat(event.chat.id)
	logging.info(f"Бот исключён из чата с ID {event.chat.id}")

async def main():
	await DISPATCHER.start_polling(BOT)

if __name__== "__main__" :
	asyncio.run(main())