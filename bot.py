from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

import config
import asyncio
import pymysql

from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton

from datetime import *

password = "Jbc[L(AXneWTJ!@Z"
conn = pymysql.connect(host='localhost', user='finance_helper_admin', password=password, database='finance_helper_admin')
cursor = conn.cursor()
bot = AsyncTeleBot(config.token, state_storage=StateMemoryStorage())

class States(StatesGroup):
	WAITING_FOR_INCOME_VALUE = State()
	category_income = State()


async def close_connection():
	print("a")
	pass


@bot.message_handler(commands=['start'])
async def welcome(message):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()

	cursor.execute("SELECT * FROM data_users")
	count = cursor.fetchall()

	if str(message.chat.id) in str(data_users):
		cursor.execute(f"SELECT post FROM data_users WHERE id = {message.chat.id}")
		post = cursor.fetchone()
		if post == "Директор":
			await chat_director(message)
		else:
			await chat_accountant(message)
	else:
		if len(count) < 2:
			markup = InlineKeyboardMarkup(row_width=2)
			item1 = InlineKeyboardButton("Руководитель", callback_data="director")
			item2 = InlineKeyboardButton("Бухгалтер", callback_data="accountant")
			markup.add(item1, item2)
			await bot.send_message(message.chat.id, "Приветствую!\nЯ - бот для небольшой компании, упрощающий жизнь бухгалтерам и их руководителям,\nпомогаю вести"
											"учет расходов и доходов.", reply_markup=markup)
		else:
			await close_connection()


@bot.callback_query_handler(lambda call: call.data in ["director", "accountant"])
async def callback(call):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()
	print(call.message.chat.id)
	if str(call.message.chat.id) not in str(data_users):
		if call.data == "director":
			"""cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (call.message.chat.id, "Директор"))
			conn.commit()
			"""
			await director(call.message)
		else:
			"""cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (call.message.chat.id, "Бухгалтер"))
			conn.commit()"""
			await accountant(call.message)
	else:
		await close_connection()


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
	cursor.execute(f"SELECT post FROM data_users WHERE id = {message.chat.id}")
	check = cursor.fetchone()
	if str(check) == "Директор":
		markup = ReplyKeyboardMarkup(resize_keyboard=True)
		item1 = KeyboardButton("Управление персоналом")
		item2 = KeyboardButton("Просмотр отчётов")
		item3 = KeyboardButton("Просмотр операций")
		markup.add(item1, item2, item3)
		await bot.send_message(message.chat.id, "Выберите одну из функций ниже.",
									   reply_markup=markup)


@bot.message_handler(content_types=['text'])
async def chat_accountant(message):
	markup = InlineKeyboardMarkup(row_width=2)
	item1 = InlineKeyboardButton("Ввод операций", callback_data="add_income")
	item2 = InlineKeyboardButton("Редактирование операций", callback_data="edit_operation")
	item3 = InlineKeyboardButton("Формирование отчётов", callback_data="create_report")
	markup.add(item1, item2, item3)
	await bot.send_message(message.chat.id, "Выберите одну из функций ниже.",
								   reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data in ["add_income", "add_expense"])
async def callback_add_operation(call):
	if call.data == "add_income":
		await bot.set_state(call.message.from_user.id, States.WAITING_FOR_INCOME_VALUE, call.message.chat.id)
		print("состояние установлено")
		async with bot.retrieve_data(call.message.from_user.id, call.message.chat.id) as data:
			data["action"] = "value_reg"
		await bot.send_message(call.message.chat.id, "Введите числовое значение операции")


@bot.message_handler(state=States.WAITING_FOR_INCOME_VALUE)
async def income_value(message):
	print(f"Получено сообщение {message} в состоянии")
	value = float(message.text)

	await bot.delete_state(message.from_user.id, message.chat.id)
	print("состояние удалено 2")

"""	await bot.set_state(message.from_user.id, States.category_income, message.chat.id)
	print("состояние установлено 2")
	await bot.send_message(message.chat.id, "Укажите категорию операции (пополнение от... / еженедельная прибыль и т.п.)")"""



@bot.message_handler(state=States.category_income)
async def set_category(message):
	category = str(message.text)

	cursor.execute("INSERT INTO incomes VALUES (%s, %s, %s)", (datetime.datetime, income_value.value, category))
	conn.commit()

	await bot.send_message(message.chat.id, "Операция успешно добавлена в БД")
	await bot.delete_state(message.from_user.id, message.chat.id)


asyncio.run(bot.polling())