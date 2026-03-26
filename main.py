from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from private import BOT_TOKEN
from helper import *

import asyncio
import logging

logging.basicConfig(level=logging.INFO, filename="log.log", filemode="w+")

BOT = Bot(token=BOT_TOKEN)
DISPATCHER = Dispatcher()

# /start
@DISPATCHER.message(Command("start"))
async def start_command(message: Message):
	return await message.answer("Привет! Я бот-модератор. Используйте /ban (в ответ на сообщение) для бана, /mute (в ответ на сообщение) для мута.")

# /ban
@DISPATCHER.message(Command("ban"))
async def ban_user(message: Message):
	await BAN_ACTION.run_action(message, BOT)

# /unban
@DISPATCHER.message(Command("unban"))
async def unban_user(message: Message):
	await UNBAN_ACTION.run_action(message, BOT)

# /mute
@DISPATCHER.message(Command("mute"))
async def mute_user(message: Message):
	await MUTE_ACTION.run_action(message, BOT)

# /unmute
@DISPATCHER.message(Command("unmute"))
async def unmute_user(message: Message):
	await UNMUTE_ACTION.run_action(message, BOT)

# /ping
@DISPATCHER.message(Command("ping"))
async def on_ping(message: Message):
	return await message.answer(text=get_ping_message())

# /debug
@DISPATCHER.message(Command("debug"))
async def on_debug(message: Message):
	# Тест на идиота 🤡
	if message.from_user == None:
		return await message.answer("Отправитель не отправитель 🤡.")
	
	msg_dict = {
		"user_id": message.from_user.id,
		"has_reply_message": message.reply_to_message != None
	}

	if message.reply_to_message == None:
		return await message.answer(f"Вы не ответили на сообщение\n\n{msg_dict}")

	return await message.answer(f"Штатная ситуация\n\n{msg_dict}")

@DISPATCHER.message()
async def dispatch_message(message: Message):
	if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
		return

	if message.from_user == None:
		return

	if message.from_user.is_bot:
		return

	if contains_bad_words(message.text):
		_ = await message.delete()
		_ = await message.answer(
			f"Пользователь {message.from_user.full_name}, не используйте ненормативную лексику!",
			delete_in_seconds=5
		)
		
		logging.info(f"Удалено сообщение от {message.from_user.id} за мат: {message.text}")
	elif random.randint(0, 1000) / 10 < FUNNY_EVENT_CHANCE:
		logging.info("Весёлое событие в ответ на сообщение")
		return await message.answer(get_ping_message())

# Запdуск бота
async def main():
	await DISPATCHER.start_polling(BOT)  # pyright: ignore[reportUnknownMemberType]

if __name__== "__main__" :
	asyncio.run(main())