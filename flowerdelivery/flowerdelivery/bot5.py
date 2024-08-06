import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

import requests
import json
from settings import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = BOT_TOKEN
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

STATUS_CHOICES = {
        'Ordered': 'Оформлен',
        'In Progress': 'В работе',
        'Delivering': 'Доставляется',
        'Completed': 'Завершен',
    }

class OrderForm(StatesGroup):
    telegram_id = State()
    category = State()
    product = State()
    quantity = State()
    more_products = State()
    address = State()
    telephone = State()
    delivery_date = State()
    delivery_time = State()
    confirm_order = State()
    order_status = State()


REGISTER_URL = 'http://127.0.0.1:8000/accounts/api/register/'
@dp.message(Command("registration"))
async def registration(message: types.Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name

    # Отправка данных на сайт для регистрации
    response = requests.post(REGISTER_URL, json={
        'telegram_id': telegram_id,
        'name': name
    })

    if response.status_code == 200:
        await message.answer("Вы успешно зарегистрированы!")
    elif response.status_code == 400 and response.json().get('error') == 'Пользователь уже существует':
        await message.answer("Вы уже зарегистрированы!")
    else:
        await message.answer(f"Ошибка регистрации. Попробуйте снова. Код ошибки: {response.status_code}")



def is_user_registered(email):
    try:
        response = requests.get(f'http://127.0.0.1:8000/accounts/api/check_user_exists/', params={'email': email})
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('exists', False), response_data.get('user_id')
    except requests.RequestException as e:
        logger.error(f"Error checking user registration: {e}")
        return False, None

def is_user_registered_tg(telegram_id):
    try:
        response = requests.get(f'http://127.0.0.1:8000/accounts/api/check_user_exists_tg/', params={'telegram_id': telegram_id})
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('exists', False), response_data.get('user_id')
    except requests.RequestException as e:
        logger.error(f"Ошибка проверки регистрации пользователя: {e}")
        return False, None


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Приветствую в FlowerDelivery Bot!\n"
        "Для просмотра каталога цветов используйте команду /catalog.\n"
        "Для оформления заказа используйте команду /order."
    )


def create_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="confirm_no")]
        ]
    )
    return keyboard

def create_confirm_ord_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="confirm_ord_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="confirm_ord_no")]
        ]
    )
    return keyboard


def create_category_keyboard(categories):
    keyboard_buttons = []
    for category in categories:
        button = InlineKeyboardButton(
            text=category['name'],
            callback_data=f"category_{category['id']}"
        )
        keyboard_buttons.append([button])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def create_product_keyboard(products):
    keyboard_buttons = [
        [KeyboardButton(text=f"{product['name']} - {product['price']}")] for product in products
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    return keyboard


@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "Вы находитесь в FlowerDelivery Bot - доставка цветов!\n\n"
        "Для просмотра категорий и товаров используйте команду /catalog.\n"
        "Для оформления заказа используйте команду /order и следуйте инструкциям.\n"
        "Для регистрации используйте команду /registration.\n"
        "Для просмотра статуса заказа используйте команду /status номер_заказа"
    )
    await message.answer(help_text)
@dp.message(Command("catalog"))
async def show_catalog(message: types.Message):
    logger.info("Received /catalog command from user %s", message.from_user.username)

    try:
        response = requests.get('http://127.0.0.1:8000/api/categories/')
        response.raise_for_status()
        categories = response.json()
        logger.info("Received categories: %s", categories)

        keyboard = create_category_keyboard(categories)
        await message.answer("Пожалуйста, выберите категорию:", reply_markup=keyboard)
    except requests.RequestException as e:
        await message.answer("Не удалось получить список категорий. Попробуйте позже.")
        logger.error(f"Failed to fetch categories: {e}")


@dp.message(Command("order"))
async def start_order_process(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    registered, user_id = is_user_registered_tg(telegram_id)

    if not registered:
        logger.info("Наша регистрация: %s", registered)
        response = requests.post(REGISTER_URL, json={
            'telegram_id': telegram_id,
            'name': message.from_user.full_name
        })
        if response.status_code == 200:
            await message.answer(
                "Вы успешно зарегистрированы! Пожалуйста, начните оформление заказа заново, используя команду /order.")
            return
        else:
            await message.answer(
                "Не удалось зарегистрировать вас. Пожалуйста, используйте команду /registration для регистрации, а затем попробуйте снова.")
            return

    await state.update_data(user_id=user_id)
    #await message.answer("Проверка прошла успешно! Пожалуйста, выберите категорию для вашего заказа.")

    try:
        response = requests.get('http://127.0.0.1:8000/api/categories/')
        response.raise_for_status()
        categories = response.json()
        logger.info("Получены следующие категории товаров: %s", categories)

        keyboard = create_category_keyboard(categories)
        await message.answer("Пожалуйста, выберите категорию:", reply_markup=keyboard)
        await state.set_state(OrderForm.category)
    except requests.RequestException as e:
        await message.answer("Не удалось получить список категорий. Попробуйте позже.")
        logger.error(f"Failed to fetch categories: {e}")


@dp.callback_query(lambda c: c.data and c.data.startswith('category_'))
async def choose_product_for_order(callback_query: CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[1])
    await state.update_data(category_id=category_id)
    logger.info(f"Пользователь выбрал категорию товаров ID: {category_id}")

    try:
        response = requests.get(f'http://127.0.0.1:8000/api/products/', params={'category': category_id})
        response.raise_for_status()
        products = response.json()
        logger.info("Products received: %s", products)

        await state.update_data(products=products)

        for product in products:
            image_path = product.get('image')

            if image_path:
                image_url = "https://www.funnyart.club/uploads/posts/2023-06/1685958631_funnyart-club-p-chudesnii-buket-tsvetov-tsveti-1.jpg"
                logger.info(f"Sending photo with URL: {image_url}")

                try:
                    await bot.send_photo(callback_query.from_user.id, photo=image_url,
                                         caption=f"{product['name']} - {product['price']}")
                except Exception as e:
                    await bot.send_message(callback_query.from_user.id, f"Ошибка при отправке изображения: {e}")
            else:
                await bot.send_message(callback_query.from_user.id,
                                       f"Изображение для товара {product['name']} отсутствует.")

        if await state.get_state() != OrderForm.category.state:
            await callback_query.answer("Вы не в режиме заказа.")
        else:
            keyboard = create_product_keyboard(products)
            await bot.send_message(callback_query.from_user.id, "Пожалуйста, выберите продукт:", reply_markup=keyboard)
            await state.set_state(OrderForm.product)

        logger.info(f"Sent product choices to user {callback_query.from_user.username}")
        await bot.answer_callback_query(callback_query.id)
    except requests.RequestException as e:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить список товаров. Попробуйте позже.")
        logger.error(f"Failed to fetch products: {e}")


@dp.message(OrderForm.product)
async def enter_quantity(message: types.Message, state: FSMContext):
    selected_product_name = message.text.split(' - ')[0]
    data = await state.get_data()
    products = data.get('products')
    selected_product = next((p for p in products if p['name'] == selected_product_name), None)

    if not selected_product:
        await message.answer("Пожалуйста, выберите продукт из предложенного списка.")
        return

    await state.update_data(selected_product=selected_product)
    await message.answer(f"Вы выбрали {selected_product_name}. Введите количество:")
    await state.set_state(OrderForm.quantity)


@dp.message(OrderForm.quantity)
async def add_more_products(message: types.Message, state: FSMContext):
    quantity = message.text
    if not quantity.isdigit() or int(quantity) <= 0:
        await message.answer("Пожалуйста, введите корректное количество (положительное число).")
        return

    data = await state.get_data()
    selected_product = data.get('selected_product')
    items = data.get('items', [])
    items.append({
        'product': selected_product['id'],
        'quantity': int(quantity),
        'price': selected_product['price']
    })
    await state.update_data(items=items)

    await message.answer("Хотите добавить еще один товар?", reply_markup=create_confirm_keyboard())
    await state.set_state(OrderForm.more_products)


@dp.callback_query(lambda c: c.data and c.data == 'confirm_yes')
async def process_more_products(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id,
                           "Пожалуйста, выберите категорию для вашего дополнительного товара.")

    try:
        response = requests.get('http://127.0.0.1:8000/api/categories/')
        response.raise_for_status()
        categories = response.json()
        logger.info("Получены следующие категории товаров: %s", categories)

        keyboard = create_category_keyboard(categories)
        await bot.send_message(callback_query.from_user.id, "Пожалуйста, выберите категорию:", reply_markup=keyboard)
        await state.set_state(OrderForm.category)
    except requests.RequestException as e:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить список категорий. Попробуйте позже.")
        logger.error(f"Failed to fetch categories: {e}")


@dp.callback_query(lambda c: c.data and c.data == 'confirm_no')
async def finalize_order_details(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Введите контактный телефон:")
    await state.set_state(OrderForm.telephone)
    await bot.answer_callback_query(callback_query.id)

@dp.message(OrderForm.telephone)
async def enter_telephone(message: types.Message, state: FSMContext):
    telephone = message.text
    await state.update_data(telephone=telephone)
    await message.answer("Введите адрес доставки:")
    await state.set_state(OrderForm.address)


@dp.message(OrderForm.address)
async def choose_delivery_date(message: types.Message, state: FSMContext):
    address = message.text
    await state.update_data(address=address)

    today = datetime.today() + timedelta(days=1)
    dates = [today + timedelta(days=i) for i in range(8)]  # Генерируем 8 дат
    keyboard_buttons = []

    for i in range(0, len(dates), 4):
        row = [
            InlineKeyboardButton(text=f" {date.strftime('%d-%m')} ",
                                 callback_data=f"date_{date.strftime('%Y-%m-%d')}")
            for date in dates[i:i + 4]
        ]
        keyboard_buttons.append(row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer("Выберите дату доставки:", reply_markup=keyboard)
    await state.set_state(OrderForm.delivery_date)


@dp.callback_query(lambda c: c.data and c.data.startswith('date_'))
async def choose_delivery_time(callback_query: CallbackQuery, state: FSMContext):
    delivery_date = callback_query.data.split('_')[1]
    await state.update_data(delivery_date=delivery_date)



    hours = list(range(9, 21))  # Диапазон от 9 до 20
    keyboard_buttons = []
    for hour in hours:
        time_text = f"{hour:02d}:00"
        button = InlineKeyboardButton(text=f" {time_text} ", callback_data=f"time_{time_text}")
        keyboard_buttons.append(button)

    # Разделяем кнопки на 3 строки по 4 времени
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        keyboard_buttons[:4],
        keyboard_buttons[4:8],
        keyboard_buttons[8:]
    ])


    await bot.send_message(callback_query.from_user.id, "Выберите время доставки:", reply_markup=keyboard)
    await state.set_state(OrderForm.delivery_time)
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query(lambda c: c.data and c.data.startswith('time_'))
async def confirm_order(callback_query: CallbackQuery, state: FSMContext):
    delivery_time = callback_query.data.split('_')[1]
    await state.update_data(delivery_time=delivery_time)

    data = await state.get_data()
    items = data.get('items')

   # выведем весь заказ на экран, чтобы покупатель его подтвердил
    order_summary = (
        f"Подтвердите ваш заказ:\n\n"
        #f"Email: {data['email']}\n"
        f"Номер телефона: {data['telephone']}\n"
        f"Адрес доставки: {data['address']}\n"
        f"Дата доставки: {data['delivery_date']}\n"
        f"Время доставки: {data['delivery_time']}\n\n"
        f"Товары:\n"
    )

    for item in data['items']:
        product = next((p for p in data['products'] if p['id'] == item['product']), None)
        if product:
            order_summary += f"{product['name']} - {item['quantity']} шт. - {item['price']} руб./шт.\n"

    total_amount = str(sum(item['quantity'] * float(item['price']) for item in data['items']))
    order_summary += f"\nОбщая сумма: {total_amount} руб."

    #await message.answer(order_summary, reply_markup=create_confirm_keyboard())
    await bot.send_message(callback_query.from_user.id, order_summary, reply_markup=create_confirm_ord_keyboard())

    await state.set_state(OrderForm.confirm_order)

@dp.callback_query(lambda c: c.data and c.data == 'confirm_ord_yes')
async def process_order(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    address = data.get('address')
    telephone = data.get('telephone')
    delivery_date = data.get('delivery_date')
    delivery_time = data.get('delivery_time')
    #email = data.get('email')
    #telegram_id = data.get('telegram_id')
    user_id = data.get('user_id')
    items = data.get('items')

    total_amount = str(sum(item['quantity'] * float(item['price']) for item in items))

    order_data = {
        'user': user_id,
        'delivery_date': delivery_date,
        'delivery_time': delivery_time,
        'address': address,
        'contact': '-',
        'telephone': telephone,
        'total_amount': total_amount,
        'status': 'Ordered',
        'items': items
    }

    logger.info(f"Отправляемые данные заказа: {json.dumps(order_data, indent=2)}")

    try:
        response = requests.post('http://127.0.0.1:8000/orders/api/orders/', json=order_data)
        response.raise_for_status()
        order_response = response.json()
        order_id = order_response.get('id')

        await bot.send_message(callback_query.from_user.id, f"Ваш заказ № {order_id} был успешно оформлен!")
        await state.clear()
    except requests.RequestException as e:
        await bot.send_message(callback_query.from_user.id, "Не удалось оформить заказ. Попробуйте позже.")
        logger.error(f"Failed to create order: {e}")

    await bot.answer_callback_query(callback_query.id)


@dp.callback_query(lambda c: c.data and c.data == 'confirm_ord_no')
async def cancel_order(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Заказ был отменен.")
    await state.clear()
    await bot.answer_callback_query(callback_query.id)


@dp.message(Command("status"))
async def get_order_status(message: types.Message):
    API_URL = 'http://127.0.0.1:8000/orders/api/order_status/'

    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.reply("Пожалуйста, укажите номер заказа. Пример: /status 123")
        return

    order_id = command_parts[1]
    if not order_id.isdigit():
        await message.reply("Пожалуйста, укажите корректный номер заказа.")
        return

    response = requests.get(f'{API_URL}{order_id}')
    if response.status_code == 200:
        data = response.json()
        status_code = data.get('status', 'Unknown')
        status_text = STATUS_CHOICES.get(status_code, 'Неизвестный статус')
        await message.reply(f"Статус вашего заказа №{data['id']}: {status_text}")
    else:
        await message.reply("Заказ не найден или произошла ошибка.")


API_URL = 'http://127.0.0.1:8000/orders/api/user_orders/'
@dp.message(Command('orders_list'))
async def list_orders(message: types.Message):
    telegram_id = message.from_user.id
    response = requests.get(API_URL, params={'telegram_id': telegram_id})

    if response.status_code == 200:
        orders = response.json()
        if not orders:
            await message.reply("У вас нет заказов.")
            return

        orders_text = '\n'.join([
            f"Заказ №{order['id']}: {STATUS_CHOICES.get(order['status'], 'Неизвестный статус')} - {order['total_amount']}"
            for order in orders
        ])
        await message.reply(f"Ваши заказы:\n{orders_text}")
    else:
        await message.reply("Произошла ошибка при получении заказов.")

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
