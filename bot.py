from telebot.async_telebot import AsyncTeleBot
import config
import asyncio
import pymysql
from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from datetime import *


password = "Jbc[L(AXneWTJ!@Z"
conn = pymysql.connect(host='localhost', user='finance_helper_admin', password=password, database='finance_helper_admin')
cursor = conn.cursor()
bot = AsyncTeleBot(config.token)


@bot.message_handler(commands=['start'])
async def welcome(message):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()

	cursor.execute("SELECT * FROM data_users")
	count = cursor.fetchall()

	if str(message.chat.id) in str(data_users):
		await chat(message)
	else:
		if len(count) < 2:
			markup = InlineKeyboardMarkup(row_width=2)
			item1 = InlineKeyboardButton("Руководитель", callback_data="director")
			item2 = InlineKeyboardButton("Бухгалтер", callback_data="accountant")
			markup.add(item1, item2)
			await bot.send_message(message.chat.id, "Приветствую!\nЯ - бот для небольшой компании, упрощающий жизнь бухгалтерам и их руководителям,\nпомогаю вести"
											"учет расходов и доходов.", reply_markup=markup)

@bot.callback_query_handler(lambda call: True)
async def callback(call):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()
	print(call.message.chat.id)
	if str(call.message.chat.id) not in str(data_users):
		if call.data == "director":
			await director(call.message)
		else:
			await accountant(call.message)
	else:
		pass


async def director(message):
	user_id = int(message.chat.id)
	cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (user_id, "Директор"))
	conn.commit()
	await chat_director(message)


async def accountant(message):
	user_id = int(message.chat.id)
	cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (user_id, "Бухгалтер"))
	conn.commit()
	await chat_accountant(message)


@bot.message_handler(content_types=['text'])
async def chat_director(message):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()
	if str(message.chat.id) in str(data_users):
		cursor.execute(f"SELECT post FROM data_users WHERE id = {message.chat.id}")
		post = cursor.fetchone()
		if post == "Директор":
			markup = ReplyKeyboardMarkup(resize_keyboard=True)
			item1 = KeyboardButton("Управление персоналом")
			item2 = KeyboardButton("Просмотр отчётов")
			item3 = KeyboardButton("Просмотр операций")
			markup.add(item1, item2, item3)
			await bot.send_message(message.chat.id, "Выберите одну из функций ниже.",
								   reply_markup=markup)
		else:
			await bot.send_message(message.chat.id, "Недостаточно прав для выполнения данной команды!")


@bot.message_handler(content_types=['text'])
async def chat_accountant(message):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()
	if str(message.chat.id) in str(data_users):
		cursor.execute(f"SELECT post FROM data_users WHERE id = {message.chat.id}")
		post = cursor.fetchone()
		if post == "Бухгалтер":
			markup = ReplyKeyboardMarkup(resize_keyboard=True)
			item1 = KeyboardButton("Ввод операций")
			item2 = KeyboardButton("Редактирование операций")
			item3 = KeyboardButton("Формирование отчётов")
			markup.add(item1, item2, item3)
			await bot.send_message(message.chat.id, "Выберите одну из функций ниже.",
								   reply_markup=markup)
		else:
			await bot.send_message(message.chat.id, "У вас недостаточно прав для выполнения данной команды!")




asyncio.run(bot.polling())