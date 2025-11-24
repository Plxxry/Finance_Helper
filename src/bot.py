from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot import asyncio_filters
import config
import asyncio
import pymysql, sqlite3
from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton

password = "Jbc[L(AXneWTJ!@Z"
#conn = pymysql.connect(host='localhost', user='finance_helper_admin', password=password, database='finance_helper_admin')
conn = sqlite3.connect('database/finance_helper_admin.db')
cursor = conn.cursor()
bot = AsyncTeleBot(config.token, state_storage=StateMemoryStorage())


class States(StatesGroup):
	WAITING_FOR_INCOME_VALUE = State()
	WAITING_FOR_EXPENSE_VALUE = State()
	CATEGORY = State()
	STAFF_MANAGING = State()
	REPORTS_MANAGING = State()


bot.add_custom_filter(asyncio_filters.StateFilter(bot))


@bot.callback_query_handler(lambda call: call.data == "create_report")
async def create_report(call):
	cursor.execute("SELECT value FROM expenses")
	expenses_value = sum(j for i in cursor.fetchall() for j in i)

	cursor.execute("SELECT value FROM incomes")
	incomes_value = sum(j for i in cursor.fetchall() for j in i)

	if expenses_value > incomes_value:
		cursor.execute("INSERT INTO reports VALUES (NULL, CURRENT_TIMESTAMP, ?, ?)", (call.message.chat.id, f"Расход компании составил {expenses_value - incomes_value}"))
		conn.commit()
		await bot.send_message(call.message.chat.id, f"Отчёт сформирован!\n"
													 f"На момент времени {cursor.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]} расход компании составил {expenses_value - incomes_value}")
	else:
		cursor.execute("INSERT INTO reports VALUES (NULL, CURRENT_TIMESTAMP, ?, ?)", (call.message.chat.id, f"Доход компании составил {incomes_value - expenses_value}"))
		conn.commit()
		await bot.send_message(call.message.chat.id, f"Отчёт сформирован!\n"
													 f"На момент времени {cursor.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]} доход компании составил {incomes_value - expenses_value}")

	await chat_accountant(call.message)

@bot.message_handler(state=States.CATEGORY)
async def add_category(message):
	category = str(message.text)

	async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
		value = data['value']
		type_of_operation = data['type']

	await bot.send_message(message.chat.id, "Категория операции успешно записана")
	await bot.delete_state(message.from_user.id, message.chat.id)

	if type_of_operation == "income":
		cursor.execute("INSERT INTO incomes VALUES (NULL, CURRENT_TIMESTAMP, ?, ?)", (value, category))
		conn.commit()
	else:
		cursor.execute("INSERT INTO expenses VALUES (NULL, CURRENT_TIMESTAMP, ?, ?)", (value, category))
		conn.commit()

	await chat_accountant(message)


@bot.message_handler(state=States.WAITING_FOR_INCOME_VALUE)
async def enter_income_value(message):
	try:
		value = float(message.text)

		async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
			data['value'] = value
			data["type"] = "income"

		await bot.send_message(message.chat.id, f"✅ Доход в размере {value} записан!")
		await bot.send_message(message.chat.id, "Укажите категорию операции (перевод / еженедельный доход и т.п.)")
		await bot.set_state(message.from_user.id, States.CATEGORY, message.chat.id)
	except ValueError:
		await bot.send_message(message.chat.id, "❌ Ошибка! Введите числовое значение.")


@bot.message_handler(state=States.WAITING_FOR_EXPENSE_VALUE)
async def enter_expense_value(message):
	try:
		value = float(message.text)

		async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
			data['value'] = value
			data['type'] = "expense"

		await bot.send_message(message.chat.id, f"✅ Расход в размере {value} записан!")
		await bot.send_message(message.chat.id, "Укажите категорию операции (перевод / закупка материалов и т.п.)")
		#await chat_accountant(message)
		await bot.set_state(message.from_user.id, States.CATEGORY, message.chat.id)
	except ValueError:
		await bot.send_message(message.chat.id, "❌ Ошибка! Введите числовое значение.")


### РЕАКЦИЯ НА КОМАНДУ START
@bot.message_handler(commands=['start'])
async def welcome(message):
	cursor.execute("SELECT staff_id FROM data_users")
	data_users = cursor.fetchall()
	print(data_users, message.chat.id)

	cursor.execute("SELECT * FROM data_users")
	count = cursor.fetchall()

	cursor.execute("SELECT staff_id FROM data_users WHERE post = 'Директор'")
	director = cursor.fetchall()

	if str(message.chat.id) in str(data_users):
		cursor.execute(f"SELECT post FROM data_users WHERE staff_id = {message.chat.id}")
		post = cursor.fetchone()

		if str(post[0]) == "Директор":
			await chat_director(message)
		else:
			await chat_accountant(message)
	else:
		if len(count) < 4:
			if not(director):
				markup = InlineKeyboardMarkup(row_width=2)
				item1 = InlineKeyboardButton("Руководитель", callback_data="director")
				item2 = InlineKeyboardButton("Бухгалтер", callback_data="accountant")
				markup.add(item1, item2)
				await bot.send_message(message.chat.id,
									   "Приветствую!\nЯ - бот для небольшой компании, упрощающий жизнь бухгалтерам и их руководителям,\nпомогаю вести учет расходов и доходов компании.",
									   reply_markup=markup)
			else:
				markup = InlineKeyboardMarkup(row_width=2)
				item1 = InlineKeyboardButton("Бухгалтер", callback_data="accountant")
				markup.add(item1)
				await bot.send_message(message.chat.id,
									   "Приветствую!\nЯ - бот для небольшой компании, упрощающий жизнь бухгалтерам и их руководителям,\nпомогаю вести учет расходов и доходов компании.",
									   reply_markup=markup)
		else:
			await universal_handler(message)


@bot.callback_query_handler(lambda call: call.data == "add_operation")
async def add_operation(call):
	markup = InlineKeyboardMarkup(row_width=3)
	item1 = InlineKeyboardButton("Доход", callback_data="add_income")
	item2 = InlineKeyboardButton("Расход", callback_data="add_expense")
	markup.add(item1, item2)
	await bot.send_message(call.message.chat.id, "Выберите характер операции", reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data == "add_income")
async def add_income(call):
	await bot.set_state(call.from_user.id, States.WAITING_FOR_INCOME_VALUE, call.message.chat.id)
	await bot.send_message(call.message.chat.id, "Введите числовое значение операции (целое/дробное)")


@bot.callback_query_handler(lambda call: call.data == "add_expense")
async def add_expense(call):
	await bot.set_state(call.from_user.id, States.WAITING_FOR_EXPENSE_VALUE, call.message.chat.id)
	await bot.send_message(call.message.chat.id, "Введите числовое значение операции (целое/дробное)")


@bot.callback_query_handler(lambda call: call.data == "staff_manage")
async def staff_manage(call):
	cursor.execute("SELECT * FROM data_users WHERE post = 'Бухгалтер'")
	data_users = cursor.fetchall()

	await bot.set_state(call.from_user.id, States.STAFF_MANAGING, call.message.chat.id)
	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
		data["data_users"] = data_users
		data["pointer"] = 0
		print(data_users)

	if data_users:

		user_id = data_users[0][0]
		user_post = data_users[0][1]

		markup = InlineKeyboardMarkup(row_width=3)
		#item1 = InlineKeyboardButton("<-", callback_data="back")
		item2 = InlineKeyboardButton("Подробнее", callback_data="parameters")
		item3 = InlineKeyboardButton("->", callback_data="forward")
		item4 = InlineKeyboardButton("Главное меню", callback_data="main")
		markup.add( item2, item3, item4)

		await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
									text=f"Номер карточки: 1/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
									reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data in ["main", "back", "forward", "parameters"], state=States.STAFF_MANAGING)
async def director_navigation(call):
	if call.data == "main":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_director(call.message)
	elif call.data == "back":

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
			print("AAA х")
			data_users = data['data_users']
			print(data_users)
			print("BBB")
			pointer = data["pointer"]

		if pointer:
			pointer -= 1
			print('as')
			user_id = data_users[pointer][0]
			user_post = data_users[pointer][1]

			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="back")
			item2 = InlineKeyboardButton("Подробнее", callback_data="parameters")
			item3 = InlineKeyboardButton("->", callback_data="forward")
			item4 = InlineKeyboardButton("Главное меню", callback_data="main")
			markup.add(item1, item2, item3, item4)

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
								   text=f"Номер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
								   reply_markup=markup)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
				data["pointer"] = pointer

		else:

			user_id = data_users[pointer][0]
			user_post = data_users[pointer][1]

			markup = InlineKeyboardMarkup(row_width=3)
			item2 = InlineKeyboardButton("Подробнее", callback_data="parameters")
			item3 = InlineKeyboardButton("->", callback_data="forward")
			item4 = InlineKeyboardButton("Главное меню", callback_data="main")
			markup.add( item2, item3, item4)

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
										text=f"Вы в начале списка!\n\nНомер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
										reply_markup=markup)
			"""await bot.send_message(call.message.chat.id,
								   f"ID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
								   reply_markup=markup)"""

	elif call.data == "forward":

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
			print("AAA х")
			data_users = data['data_users']
			print(data_users)
			print("BBB")
			pointer = data["pointer"]

		if pointer < len(data_users) - 1:
			print("asdfd")
			pointer += 1
			user_id = data_users[pointer][0]
			user_post = data_users[pointer][1]

			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="back")
			item2 = InlineKeyboardButton("Подробнее", callback_data="parameters")
			item3 = InlineKeyboardButton("->", callback_data="forward")
			item4 = InlineKeyboardButton("Главное меню", callback_data="main")
			markup.add(item1, item2, item3, item4)

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
										text=f"Номер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
										reply_markup=markup)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
				data["pointer"] = pointer

			print(data["pointer"])
		else:

			user_id = data_users[pointer][0]
			user_post = data_users[pointer][1]

			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="back")
			item2 = InlineKeyboardButton("Подробнее", callback_data="parameters")
			item4 = InlineKeyboardButton("Главное меню", callback_data="main")
			markup.add(item1, item2, item4)

			await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
										text=f"Вы в конце списка!\nНомер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
										reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data in ["director", "accountant"])
async def callback(call):
	print("aaaaaa")
	cursor.execute("SELECT staff_id FROM data_users")
	data_users = cursor.fetchall()

	if str(call.message.chat.id) not in str(data_users):
		if call.data == "director":
			cursor.execute("INSERT INTO data_users (staff_id, post) VALUES (?, ?)", (call.message.chat.id, "Директор"))
			conn.commit()
			await chat_director(call.message)
		else:
			cursor.execute("INSERT INTO data_users (staff_id, post) VALUES (?, ?)", (call.message.chat.id, "Бухгалтер"))
			conn.commit()
			await chat_accountant(call.message)
	await bot.answer_callback_query(call.id)


async def chat_director(message):
	cursor.execute(f"SELECT post FROM data_users WHERE staff_id = {message.chat.id}")
	check = cursor.fetchone()
	print(check[0])
	if check and check[0] == "Директор":
		markup = InlineKeyboardMarkup(row_width=1)
		item1 = InlineKeyboardButton("Управление персоналом", callback_data="staff_manage")
		item2 = InlineKeyboardButton("Просмотр отчётов", callback_data="view_reports")
		item3 = InlineKeyboardButton("Просмотр операций", callback_data="view_operations")
		markup.add(item1, item2, item3)
		await bot.send_message(message.chat.id, "Выберите одну из функций ниже.", reply_markup=markup)


async def chat_accountant(message):
	cursor.execute(f"SELECT post FROM data_users WHERE staff_id = {message.chat.id}")
	check = cursor.fetchone()
	if check and check[0] == "Бухгалтер":
		markup = InlineKeyboardMarkup(row_width=1)
		item1 = InlineKeyboardButton("Ввод операций", callback_data="add_operation")
		item2 = InlineKeyboardButton("Редактирование операций", callback_data="edit_operation")
		item3 = InlineKeyboardButton("Формирование отчётов", callback_data="create_report")
		markup.add(item1, item2, item3)
		await bot.send_message(message.chat.id, "Выберите одну из функций ниже.", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
async def universal_handler(message):
	cursor.execute("SELECT * FROM data_users")

	data_users = cursor.fetchall()
	count = len(data_users)

	if count >= 2 and str(message.chat.id) not in str(data_users):
		pass
	else:
		current_state = await bot.get_state(message.from_user.id, message.chat.id)
		if not current_state:
			await bot.send_message(message.chat.id, "Извините, я вас не понял, возвращаюсь в главное меню")
			await welcome(message)


if __name__ == "__main__":
	asyncio.run(bot.polling())
else:
	conn.close()