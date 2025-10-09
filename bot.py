from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot import asyncio_filters
import config
import asyncio
import pymysql
from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton

password = "Jbc[L(AXneWTJ!@Z"
conn = pymysql.connect(host='localhost', user='finance_helper_admin', password=password, database='finance_helper_admin')
cursor = conn.cursor()
bot = AsyncTeleBot(config.token, state_storage=StateMemoryStorage())


class States(StatesGroup):
	WAITING_FOR_INCOME_VALUE = State()


bot.add_custom_filter(asyncio_filters.StateFilter(bot))


@bot.message_handler(state=States.WAITING_FOR_INCOME_VALUE)
async def enter_value(message):
	try:
		value = float(message.text)

		await bot.send_message(message.chat.id, f"✅ Доход в размере {value} записан!")
		await bot.delete_state(message.from_user.id, message.chat.id)
		await chat_accountant(message)
	except ValueError:
		await bot.send_message(message.chat.id, "❌ Ошибка! Введите числовое значение.")


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
			await bot.send_message(message.chat.id,
								   "Приветствую!\nЯ - бот для небольшой компании, упрощающий жизнь бухгалтерам и их руководителям,\nпомогаю вести учет расходов и доходов.",
								   reply_markup=markup)
		else:
			await close_connection()


@bot.callback_query_handler(lambda call: call.data == "add_income")
async def get_value(call):
	await bot.set_state(call.from_user.id, States.WAITING_FOR_INCOME_VALUE, call.message.chat.id)
	await bot.send_message(call.message.chat.id, "Введите сумму дохода:")
	await bot.answer_callback_query(call.id)


@bot.callback_query_handler(lambda call: call.data in ["director", "accountant"])
async def callback(call):
	cursor.execute("SELECT id FROM data_users")
	data_users = cursor.fetchall()

	if str(call.message.chat.id) not in str(data_users):
		if call.data == "director":
			cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (call.message.chat.id, "Директор"))
			conn.commit()
			await chat_director(call.message)
		else:
			cursor.execute("INSERT INTO data_users (id, post) VALUES (%s, %s)", (call.message.chat.id, "Бухгалтер"))
			conn.commit()
			await chat_accountant(call.message)
	await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == "Управление персоналом")
async def handle_personnel_management(message):
	await bot.send_message(message.chat.id, "Раздел управления персоналом")


@bot.message_handler(func=lambda message: message.text == "Просмотр отчётов")
async def handle_reports(message):
	await bot.send_message(message.chat.id, "Раздел просмотра отчетов")


@bot.message_handler(func=lambda message: message.text == "Просмотр операций")
async def handle_operations(message):
	await bot.send_message(message.chat.id, "Раздел просмотра операций")


async def chat_director(message):
	cursor.execute(f"SELECT post FROM data_users WHERE id = {message.chat.id}")
	check = cursor.fetchone()
	if check and check[0] == "Директор":
		markup = ReplyKeyboardMarkup(resize_keyboard=True)
		item1 = KeyboardButton("Управление персоналом")
		item2 = KeyboardButton("Просмотр отчётов")
		item3 = KeyboardButton("Просмотр операций")
		markup.add(item1, item2, item3)
		await bot.send_message(message.chat.id, "Выберите одну из функций ниже.", reply_markup=markup)


async def chat_accountant(message):
	markup = InlineKeyboardMarkup(row_width=2)
	item1 = InlineKeyboardButton("Ввод операций", callback_data="add_income")
	item2 = InlineKeyboardButton("Редактирование операций", callback_data="edit_operation")
	item3 = InlineKeyboardButton("Формирование отчётов", callback_data="create_report")
	markup.add(item1, item2, item3)
	await bot.send_message(message.chat.id, "Выберите одну из функций ниже.", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
async def universal(message):
	current_state = await bot.get_state(message.from_user.id, message.chat.id)
	if not current_state:
		await bot.send_message(message.chat.id, "Используйте кнопки для навигации")


async def close_connection():
	pass


if __name__ == "__main__":
	asyncio.run(bot.polling())