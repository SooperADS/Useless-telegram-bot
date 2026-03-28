import logging
import re

from aiogram.types import Message

from .config import *

__stopped_in_chats: set[int] = set()
"""ЛОКАЛЬНОЕ СОСТОЯНИЕ: не изменять вне модуля"""

def str_contains_bad_words(text: str) -> bool:
	"""
	Мы тута проверяем текст на наличие плохих слов
	"""
	cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
	for word in cleaned_text.split():
		if word in BAD_WORDS:
			return True

	return False

def enable_in_chat(chat_id: int):
	__stopped_in_chats.remove(chat_id)

def disable_in_chat(chat_id: int):
	__stopped_in_chats.add(chat_id)
	
def forget_chat(chat_id: int):
	"""
	Сбрасывает параметры цензора в заданном чате
	"""
	__stopped_in_chats.remove(chat_id)

def is_enable_in_chat(chat_id: int) -> bool:
	return chat_id not in __stopped_in_chats

async def apply_on_message(message: Message) -> bool:
	"""
	Применяем цензуру на заданном сообщении
	"""
	if message.from_user == None or not await message.delete():
		return False
	
	await message.answer(
		f"Пользователь **{message.from_user.full_name}**, не используйте ненормативную лексику!",
		delete_in_seconds=5
	)

	logging.info(f"Удалено сообщение от {message.from_user.id} за мат: {message.text}")
	return True

async def process_message(message: Message) -> bool:
	"""
	Обрабатываем сообщение и, при надобности, применяем цензуру
	"""
	if message.text and is_enable_in_chat(message.chat.id):
		if str_contains_bad_words(message.text):
			return await apply_on_message(message)
	
	return False
