from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from helper import *

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

# Токен бота (замените на свой)
BOT_TOKEN = "<put your token here>"

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

# /mute
@DISPATCHER.message(Command("mute"))
async def mute_user(message: Message):
	await MUTE_ACTION.run_action(message, BOT)

# /ping
@DISPATCHER.message(Command("ping"))
async def on_ping(message: Message):
	return await message.answer("Чики-брики в дамки")

@DISPATCHER.message()
async def check_message(message: Message):
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

# Запdуск бота
async def main():
	await DISPATCHER.start_polling(BOT)  # pyright: ignore[reportUnknownMemberType]

if __name__== "__main__" :
	asyncio.run(main())