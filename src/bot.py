from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot import asyncio_filters
import config
import asyncio
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

password = "Jbc[L(AXneWTJ!@Z"
#conn = pymysql.connect(host='localhost', user='finance_helper_admin', password=password, database='finance_helper_admin')
conn = sqlite3.connect('database/finance_helper_admin.db')
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

bot = AsyncTeleBot(config.token, state_storage=StateMemoryStorage())


class States(StatesGroup):
	WAITING_FOR_INCOME_VALUE = State()

	WAITING_FOR_EDITED_VALUE = State()

	WAITING_FOR_EXPENSE_VALUE = State()

	CATEGORY = State()

	NEW_CATEGORY = State()

	STAFF_MANAGING = State()
	REPORTS_MANAGING = State()
	OPERATIONS_MANAGING = State()

	CONFIRM_DELETE = State()

	VIEW_OPERATIONS = State()



bot.add_custom_filter(asyncio_filters.StateFilter(bot))

@bot.callback_query_handler(lambda call: call.data == "view_operations")
async def get_operations_type(call):
	markup = InlineKeyboardMarkup(row_width=2)
	item1 = InlineKeyboardButton("Доход", callback_data="income")
	item2 = InlineKeyboardButton("Расход", callback_data="expense")
	markup.add(item1, item2)

	await bot.edit_message_text("Выберите характер операций", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data in ["income", "expense"])
async def view_operations(call):
	pointer = 0

	if call.data == "income":
		cursor.execute("SELECT * FROM incomes")
		data = cursor.fetchall()

		id = data[pointer][0]
		time = data[pointer][1]
		value = data[pointer][2]
		desc = data[pointer][3]


		markup = InlineKeyboardMarkup(row_width=2)
		item1 = InlineKeyboardButton("Главное меню", callback_data="main")
		item2 = InlineKeyboardButton("->", callback_data="next")
		markup.add(item1, item2)

		await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
									f"Время операции - {time}\n"
									f"Значение - {value}\n"
									f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

		await bot.set_state(call.from_user.id, States.VIEW_OPERATIONS, call.message.chat.id)

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as op_data:
			op_data['pointer'] = pointer
			op_data['id'] = id
			op_data['data'] = data

	elif call.data == "expense":
		cursor.execute("SELECT * FROM expenses")
		data = cursor.fetchall()

		id = data[pointer][0]
		time = data[pointer][1]
		value = data[pointer][2]
		desc = data[pointer][3]

		markup = InlineKeyboardMarkup(row_width=2)
		item1 = InlineKeyboardButton("Главное меню", callback_data="main")
		item2 = InlineKeyboardButton("->", callback_data="next")
		markup.add(item1, item2)

		await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
									f"Время операции - {time}\n"
									f"Значение - {value}\n"
									f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

		await bot.set_state(call.from_user.id, States.VIEW_OPERATIONS, call.message.chat.id)

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as op_data:
			op_data['pointer'] = pointer
			op_data['id'] = id
			op_data['data'] = data


@bot.callback_query_handler(lambda call: call.data in ["main", "next", "prev"], state=States.VIEW_OPERATIONS)
async def operations_navigate(call):

	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as op_data:
		pointer = op_data['pointer']
		id = op_data['id']
		data = op_data['data']

	current_operation = data[pointer]

	if call.data == "main":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_director(call.message)

	if data:
		if call.data == "next":
			if pointer < len(data) - 1:
				pointer += 1

				id = current_operation[0]
				time = current_operation[1]
				value = current_operation[2]
				desc = current_operation[3]

				markup = InlineKeyboardMarkup(row_width=2)
				item0 = InlineKeyboardButton("<-", callback_data="prev")
				item1 = InlineKeyboardButton("Главное меню", callback_data="main")
				item2 = InlineKeyboardButton("->", callback_data="next")
				markup.add(item0, item1, item2)

				await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
											f"Время операции - {time}\n"
											f"Значение - {value}\n"
											f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

				async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as op_data:
					op_data['pointer'] = pointer
					op_data['id'] = id
					op_data['data'] = data

			else:
				id = current_operation[0]
				time = current_operation[1]
				value = current_operation[2]
				desc = current_operation[3]

				markup = InlineKeyboardMarkup(row_width=2)
				item0 = InlineKeyboardButton("<-", callback_data="prev")
				item1 = InlineKeyboardButton("Главное меню", callback_data="main")
				item2 = InlineKeyboardButton("->", callback_data="next")
				markup.add(item0, item1)

				await bot.edit_message_text(f"Вы в конце списка!\nНомер карточки: {pointer + 1}/{len(data)}\n\n"
											f"Время операции - {time}\n"
											f"Значение - {value}\n"
											f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

		elif call.data == "prev":
			if pointer > 0:
				pointer -= 1

				id = current_operation[0]
				time = current_operation[1]
				value = current_operation[2]
				desc = current_operation[3]

				markup = InlineKeyboardMarkup(row_width=2)
				item0 = InlineKeyboardButton("<-", callback_data="prev")
				item1 = InlineKeyboardButton("Главное меню", callback_data="main")
				item2 = InlineKeyboardButton("->", callback_data="next")
				markup.add(item0, item1, item2)

				await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
											f"Время операции - {time}\n"
											f"Значение - {value}\n"
											f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

				async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as op_data:
					op_data['pointer'] = pointer
					op_data['id'] = id
					op_data['data'] = data

			else:
				id = current_operation[0]
				time = current_operation[1]
				value = current_operation[2]
				desc = current_operation[3]

				markup = InlineKeyboardMarkup(row_width=2)
				item0 = InlineKeyboardButton("<-", callback_data="prev")
				item1 = InlineKeyboardButton("Главное меню", callback_data="main")
				item2 = InlineKeyboardButton("->", callback_data="next")
				markup.add(item1, item2)

				await bot.edit_message_text(f"Вы в начале списка!\nНомер карточки: {pointer + 1}/{len(data)}\n\n"
											f"Время операции - {time}\n"
											f"Значение - {value}\n"
											f"Категория - {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)
	else:
		await bot.edit_message_text("Список пуст!", call.message.chat.id, call.message.id)
		await chat_director(call.message)


@bot.callback_query_handler(lambda call: call.data == "view_reports")
async def reports(call):

	cursor.execute("SELECT * FROM reports")
	data = cursor.fetchall()
	print(data)
	if data:
		pointer = 0
		id = data[pointer][0]
		time = data[pointer][1]
		accountant_id = data[pointer][2]
		desc = data[pointer][3]

		markup = InlineKeyboardMarkup(row_width=3)
		#item1 = InlineKeyboardButton("<-", callback_data="prev_rep")
		item2 = InlineKeyboardButton("->", callback_data="next_rep")
		item3 = InlineKeyboardButton("Главное меню", callback_data="go_main_menu")
		markup.add(item3, item2)

		await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
									f"Автор отчёта - {accountant_id}\n"
									f"Время создания отчёта - {time}\n"
									f"Описание: {desc}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=markup)

		await bot.set_state(call.from_user.id, States.REPORTS_MANAGING, call.message.chat.id)

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_rep:
			data_rep['pointer'] = pointer
			data_rep['main'] = data
	else:
		await bot.edit_message_text("Список пуст!", chat_id=call.message.chat.id, message_id=call.message.id)
		await chat_director(call.message)



@bot.callback_query_handler(lambda call: call.data in ["prev_rep", "next_rep", "go_main_menu"], state=States.REPORTS_MANAGING)
async def reports_managing(call):

	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_rep:
		pointer = data_rep['pointer']
		data = data_rep['main']

	if call.data == "prev_rep":
		if pointer:
			pointer -= 1
			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="prev_rep")
			item2 = InlineKeyboardButton("->", callback_data="next_rep")
			item3 = InlineKeyboardButton("Главное меню", callback_data="go_main_menu")
			markup.add(item1, item3, item2)

			await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
										f"Автор отчёта - {data[pointer][2]}\n"
										f"Время создания отчёта - {data[pointer][1]}\n"
										f"Описание: {data[pointer][3]}", chat_id=call.message.chat.id, message_id=call.message.id,
										reply_markup=markup)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_rep:
				data_rep['pointer'] = pointer
				data_rep['main'] = data

		else:
			markup = InlineKeyboardMarkup(row_width=3)
			#item1 = InlineKeyboardButton("<-", callback_data="prev_rep")
			item2 = InlineKeyboardButton("->", callback_data="next_rep")
			item3 = InlineKeyboardButton("Главное меню", callback_data="go_main_menu")
			markup.add(item3, item2)

			await bot.edit_message_text(f"Вы в начале списка!\n"
										f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
										f"Автор отчёта - {data[pointer][2]}\n"
										f"Время создания отчёта - {data[pointer][1]}\n"
										f"Описание: {data[pointer][3]}", chat_id=call.message.chat.id,
										message_id=call.message.id,
										reply_markup=markup)
	elif call.data == "next_rep":
		if pointer < len(data) - 1:

			pointer += 1
			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="prev_rep")
			item2 = InlineKeyboardButton("->", callback_data="next_rep")
			item3 = InlineKeyboardButton("Главное меню", callback_data="go_main_menu")
			markup.add(item1, item3, item2)

			await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
										f"Автор отчёта - {data[pointer][2]}\n"
										f"Время создания отчёта - {data[pointer][1]}\n"
										f"Описание: {data[pointer][3]}", chat_id=call.message.chat.id, message_id=call.message.id,
										reply_markup=markup)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_rep:
				data_rep['pointer'] = pointer
				data_rep['main'] = data

		else:
			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("<-", callback_data="prev_rep")
			#item2 = InlineKeyboardButton("->", callback_data="next_rep")
			item3 = InlineKeyboardButton("Главное меню", callback_data="go_main_menu")
			markup.add(item1, item3)

			await bot.edit_message_text(f"Вы в конце списка!\n"
										f"Номер карточки: {pointer + 1}/{len(data)}\n\n"
										f"Автор отчёта - {data[pointer][2]}\n"
										f"Время создания отчёта - {data[pointer][1]}\n"
										f"Описание: {data[pointer][3]}", chat_id=call.message.chat.id,
										message_id=call.message.id,
										reply_markup=markup)
	elif call.data == "go_main_menu":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_director(call.message)


@bot.callback_query_handler(lambda call: call.data in ['cancel_confirming', 'go_confirming'], state=States.CONFIRM_DELETE)
async def delete_user(call):
	if call.data == "cancel_confirming":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_director(call.message)
	else:
		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_user:
			user_id = data_user['wid']

		cursor.execute(f"DELETE FROM data_users WHERE staff_id = {user_id}")
		conn.commit()

		await bot.edit_message_text("Пользователь удалён.", call.message.chat.id, call.message.id)
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await chat_director(call.message)


@bot.callback_query_handler(lambda call: call.data == "edit_operation")
async def type_of_operation(call):

	markup = InlineKeyboardMarkup(row_width=3)
	item1 = InlineKeyboardButton("Доход", callback_data="edit_income")
	item2 = InlineKeyboardButton("Расход", callback_data="edit_expense")
	item3 = InlineKeyboardButton("Главное меню", callback_data="return_to_main")
	markup.add(item1, item2, item3)
	await bot.edit_message_text(f"Выберите тип операции", reply_markup=markup, chat_id=call.message.chat.id, message_id=call.message.id)
	await bot.set_state(call.from_user.id, States.OPERATIONS_MANAGING, call.message.chat.id)

	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as editing_data:
		editing_data["pointer"] = 0


@bot.callback_query_handler(lambda call: call.data in ["edit_income", "edit_expense", "return_to_main"], state=States.OPERATIONS_MANAGING)
async def operations_navigate(call):

	if call.data == "edit_income":

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as editing_data:
			pointer = editing_data["pointer"]
			editing_data["table_name"] = "incomes"
			editing_data["type_of_operations"] = "Доход"

		cursor.execute("SELECT * FROM incomes")
		data_incomes = cursor.fetchall()

		if data_incomes:
			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item1, item2, item3, item4, item5)
			await bot.edit_message_text(f"Номер карточки: 1/{len(data_incomes)}\n\n"
										f"Время операции - {data_incomes[pointer][1]}\n"
										f"Значение - {data_incomes[pointer][2]}\n"
										f"Тип операции - Доход\n"
										f"Категория - {data_incomes[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)
		else:
			await bot.send_message(call.message.chat.id, "Список пуст!")
			await chat_accountant(call.message)

	elif call.data == "edit_expense":

		async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as editing_data:
			pointer = editing_data["pointer"]
			editing_data["table_name"] = "expenses"
			editing_data['type_of_operations'] = "Расход"

		cursor.execute("SELECT * FROM expenses")
		data_expenses = cursor.fetchall()

		if data_expenses:
			markup = InlineKeyboardMarkup(row_width=3)
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item1, item2, item3, item4, item5)
			await bot.edit_message_text(f"Номер карточки: 1/{len(data_expenses)}\n\n"
										f"Время операции - {data_expenses[pointer][1]}\n"
										f"Значение - {data_expenses[pointer][2]}\n"
										f"Тип операции - Доход\n"
										f"Категория - {data_expenses[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)
		else:
			await bot.send_message(call.message.chat.id, "Список пуст!")
			await chat_accountant(call.message)

	elif call.data == "return_to_main":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_accountant(call.message)


@bot.callback_query_handler(lambda call: call.data in ["delete", "edit_value", "edit_category", "next", "prev", "go_main"], state=States.OPERATIONS_MANAGING)
async def manage_operations(call):

	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
		type = data["table_name"]
		pointer = data["pointer"]


	cursor.execute(f"SELECT * FROM {type}")
	data_operations = cursor.fetchall()
	current_operation = data_operations[pointer]


	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
		data["id"] = current_operation[0]


	if call.data == "delete":
		cursor.execute(f"DELETE FROM {type} WHERE writing_id = {current_operation[0]}")
		conn.commit()

		await bot.edit_message_text(f"Запись успешно удалена!", chat_id=call.message.chat.id, message_id=call.message.id)
		await chat_accountant(call.message)

	elif call.data == "edit_value":
		await bot.set_state(call.from_user.id, States.WAITING_FOR_EDITED_VALUE, call.message.chat.id)
		await bot.edit_message_text("Пожалуйста, введите новое значение", message_id=call.message.id, chat_id=call.message.chat.id)

	elif call.data == "edit_category":
		await bot.edit_message_text("Пожалуйста, введите новую категорию", message_id=call.message.id, chat_id=call.message.chat.id)
		await bot.set_state(call.from_user.id, States.NEW_CATEGORY, call.message.chat.id)

	elif call.data == "next":
		if pointer < len(data_operations) - 1:

			pointer += 1

			markup = InlineKeyboardMarkup(row_width=3)
			item0 = InlineKeyboardButton("<-", callback_data="prev")
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item0, item1, item2, item3, item4, item5)
			await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data_operations)}\n\n"
										f"Время операции - {data_operations[pointer][1]}\n"
										f"Значение - {data_operations[pointer][2]}\n"
										f"Тип операции - {data['type_of_operations']}\n"
										f"Категория - {data_operations[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
				data["pointer"] = pointer
				data['id'] = current_operation[0]


		else:
			markup = InlineKeyboardMarkup(row_width=3)
			item0 = InlineKeyboardButton("<-", callback_data="prev")
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item0, item1, item2, item3, item5)
			await bot.edit_message_text(f"Вы в конце списка!\n"
										f"Номер карточки: {pointer + 1}/{len(data_operations)}\n\n"
										f"Время операции - {data_operations[pointer][1]}\n"
										f"Значение - {data_operations[pointer][2]}\n"
										f"Тип операции - {data['type_of_operations']}\n"
										f"Категория - {data_operations[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)


	elif call.data == "prev":
		if pointer > 0:
			pointer -= 1

			markup = InlineKeyboardMarkup(row_width=3)
			item0 = InlineKeyboardButton("<-", callback_data="prev")
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item0, item1, item2, item3, item4, item5)
			await bot.edit_message_text(f"Номер карточки: {pointer + 1}/{len(data_operations)}\n\n"
										f"Время операции - {data_operations[pointer][1]}\n"
										f"Значение - {data_operations[pointer][2]}\n"
										f"Тип операции - {data['type_of_operations']}\n"
										f"Категория - {data_operations[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)

			async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
				data["pointer"] = pointer
				data['id'] = current_operation[0]
		else:
			markup = InlineKeyboardMarkup(row_width=3)
			item0 = InlineKeyboardButton("<-", callback_data="prev")
			item1 = InlineKeyboardButton("Удалить запись", callback_data="delete")
			item2 = InlineKeyboardButton("Изменить значение", callback_data="edit_value")
			item3 = InlineKeyboardButton("Изменить категорию", callback_data="edit_category")
			item4 = InlineKeyboardButton("->", callback_data="next")
			item5 = InlineKeyboardButton("Главное меню", callback_data="go_main")
			markup.add(item1, item2, item3, item4, item5)
			await bot.edit_message_text(f"Вы в начале списка!\n"
										f"Номер карточки: {pointer + 1}/{len(data_operations)}\n\n"
										f"Время операции - {data_operations[pointer][1]}\n"
										f"Значение - {data_operations[pointer][2]}\n"
										f"Тип операции - {data['type_of_operations']}\n"
										f"Категория - {data_operations[pointer][3]}\n\n"
										f"Выберите действие", reply_markup=markup, chat_id=call.message.chat.id,
										message_id=call.message.id)

	elif call.data == "go_main":
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await bot.delete_message(call.message.chat.id, call.message.id)
		await chat_accountant(call.message)



@bot.message_handler(state=States.WAITING_FOR_EDITED_VALUE)
async def enter_new_value(message):

	async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
		type = data["type_of_operations"]
		table_name = data["table_name"]
		pointer = data["pointer"]
		wid = data["id"]

	try:
		new_value = float(message.text)


		cursor.execute(f"UPDATE {table_name} SET value = {new_value} WHERE writing_id = {wid}")
		conn.commit()

		await bot.send_message(message.chat.id, "Новые данные успешно добавлены!")
		await bot.delete_state(message.from_user.id, message.chat.id)
		await chat_accountant(message)

	except ValueError:
		await bot.edit_message_text("Ошибка! Введите числовое значение", message.chat.id, message.id)


@bot.message_handler(state=States.NEW_CATEGORY)
async def update_category(message):

	async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
		type = data["type_of_operations"]
		table_name = data["table_name"]
		pointer = data["pointer"]
		wid = data["id"]

	new_category = str(message.text)

	cursor.execute(f"UPDATE {table_name} SET category = '{new_category}' WHERE writing_id = {wid}")
	conn.commit()

	await bot.send_message(message.chat.id, "Новые данные успешно добавлены!")
	await bot.delete_state(message.from_user.id, message.chat.id)
	await chat_accountant(message)

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
		data["wid"] = data_users[0][0]
		print(data_users)

	if data_users:

		user_id = data_users[0][0]
		user_post = data_users[0][1]

		markup = InlineKeyboardMarkup(row_width=3)
		#item1 = InlineKeyboardButton("<-", callback_data="back")
		item2 = InlineKeyboardButton("Удалить сотрудника", callback_data="delete_user")
		item3 = InlineKeyboardButton("->", callback_data="forward")
		item4 = InlineKeyboardButton("Главное меню", callback_data="main")
		markup.add( item2, item3, item4)

		await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
									text=f"Номер карточки: 1/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
									reply_markup=markup)
	else:
		await bot.edit_message_text("Список пуст!", call.message.chat.id, call.message.id)
		await chat_director(call.message)

@bot.callback_query_handler(lambda call: call.data in ["main", "back", "forward", "delete_user"], state=States.STAFF_MANAGING)
async def director_navigation(call):
	async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
		data_users = data['data_users']
		pointer = data["pointer"]

	if data_users:

		if call.data == "main":
			await bot.delete_state(call.from_user.id, call.message.chat.id)
			await bot.delete_message(call.message.chat.id, call.message.id)
			await chat_director(call.message)

		elif call.data == "back":

			if pointer:
				pointer -= 1
				user_id = data_users[pointer][0]
				user_post = data_users[pointer][1]

				markup = InlineKeyboardMarkup(row_width=3)
				item1 = InlineKeyboardButton("<-", callback_data="back")
				item2 = InlineKeyboardButton("Удалить сотрудника", callback_data="delete_user")
				item3 = InlineKeyboardButton("->", callback_data="forward")
				item4 = InlineKeyboardButton("Главное меню", callback_data="main")
				markup.add(item1, item2, item3, item4)

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
									   text=f"Номер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
									   reply_markup=markup)

				async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
					data["pointer"] = pointer
					data['wid'] = user_id

			else:

				user_id = data_users[pointer][0]
				user_post = data_users[pointer][1]

				markup = InlineKeyboardMarkup(row_width=3)
				item2 = InlineKeyboardButton("Удалить сотрудника", callback_data="delete_user")
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

			if pointer < len(data_users) - 1:
				pointer += 1
				user_id = data_users[pointer][0]
				user_post = data_users[pointer][1]

				markup = InlineKeyboardMarkup(row_width=3)
				item1 = InlineKeyboardButton("<-", callback_data="back")
				item2 = InlineKeyboardButton("Удалить сотрудника", callback_data="delete_user")
				item3 = InlineKeyboardButton("->", callback_data="forward")
				item4 = InlineKeyboardButton("Главное меню", callback_data="main")
				markup.add(item1, item2, item3, item4)

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
											text=f"Номер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
											reply_markup=markup)

				async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
					data["pointer"] = pointer
					data['wid'] = user_id

			else:

				user_id = data_users[pointer][0]
				user_post = data_users[pointer][1]

				markup = InlineKeyboardMarkup(row_width=3)
				item1 = InlineKeyboardButton("<-", callback_data="back")
				item2 = InlineKeyboardButton("Удалить сотрудника", callback_data="delete_user")
				item4 = InlineKeyboardButton("Главное меню", callback_data="main")
				markup.add(item1, item2, item4)

				await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
											text=f"Вы в конце списка!\nНомер карточки: {pointer + 1}/{len(data_users)}\nID сотрудника - {user_id}\n\nДолжность сотрудника - {user_post}",
											reply_markup=markup)

		elif call.data == "delete_user":
			markup = InlineKeyboardMarkup(row_width=2)
			item1 = InlineKeyboardButton("Отмена", callback_data="cancel_confirming")
			item2 = InlineKeyboardButton("Подтвердить", callback_data="go_confirming")
			markup.add(item1, item2)

			await bot.edit_message_text("Вы точно хотите удалить сотрудника?", chat_id=call.message.chat.id,
										message_id=call.message.id, reply_markup=markup)

			await bot.set_state(call.from_user.id, States.CONFIRM_DELETE, call.message.chat.id)

	else:
		await bot.edit_message_text("Список пуст!", call.message.chat.id, call.message.id)
		await bot.delete_state(call.from_user.id, call.message.chat.id)
		await chat_director(call.message)



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