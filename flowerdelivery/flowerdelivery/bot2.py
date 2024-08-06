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


class OrderForm(StatesGroup):
    email = State()
    category = State()
    product = State()
    quantity = State()
    more_products = State()
    telephone = State()  # Добавлено состояние для телефона
    address = State()
    delivery_date = State()
    delivery_time = State()
    confirm_order = State()


def is_user_registered(email):
    try:
        response = requests.get(f'http://127.0.0.1:8000/accounts/api/check_user_exists/', params={'email': email})
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('exists', False), response_data.get('user_id')
    except requests.RequestException as e:
        logger.error(f"Error checking user registration: {e}")
        return False, None


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Приветствую в FlowerDelivery Bot! Для просмотра каталога используйте команду /catalog. Для оформления заказа используйте команду /order."
    )


def create_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="confirm_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="confirm_no")]
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
    await message.answer("Введите вашу электронную почту для проверки регистрации.")
    await state.set_state(OrderForm.email)


@dp.message(OrderForm.email)
async def get_email_for_order(message: types.Message, state: FSMContext):
    email = message.text
    registered, user_id = is_user_registered(email)
    if not registered:
        await message.answer(
            "Вы не зарегистрированы на нашем сайте. Пожалуйста, зарегистрируйтесь на сайте перед тем, как сделать заказ.")
        await state.clear()
        return

    await state.update_data(email=email, user_id=user_id)
    await message.answer("Проверка прошла успешно! Пожалуйста, выберите категорию для вашего заказа.")

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
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, введите ваш номер телефона:")
    await state.set_state(OrderForm.telephone)


@dp.message(OrderForm.telephone)
async def get_telephone(message: types.Message, state: FSMContext):
    telephone = message.text
    await state.update_data(telephone=telephone)
    await message.answer("Пожалуйста, введите адрес доставки.")
    await state.set_state(OrderForm.address)


@dp.message(OrderForm.address)
async def get_delivery_address(message: types.Message, state: FSMContext):
    address = message.text
    await state.update_data(address=address)

    today = datetime.today()
    dates = [today + timedelta(days=i) for i in range(8)]
    date_options = [date.strftime("%Y-%m-%d") for date in dates]
    date_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=date)] for date in date_options],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Введите дату доставки (выберите из предложенных вариантов):", reply_markup=date_keyboard)
    await state.set_state(OrderForm.delivery_date)


@dp.message(OrderForm.delivery_date)
async def get_delivery_time(message: types.Message, state: FSMContext):
    delivery_date = message.text
    await state.update_data(delivery_date=delivery_date)

    time_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="10:00"), KeyboardButton(text="12:00")],
            [KeyboardButton(text="14:00"), KeyboardButton(text="16:00")],
            [KeyboardButton(text="18:00"), KeyboardButton(text="20:00")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Введите время доставки (выберите из предложенных вариантов):", reply_markup=time_keyboard)
    await state.set_state(OrderForm.delivery_time)


@dp.message(OrderForm.delivery_time)
async def confirm_order(message: types.Message, state: FSMContext):
    delivery_time = message.text
    await state.update_data(delivery_time=delivery_time)

    data = await state.get_data()
    email = data.get('email')
    address = data.get('address')
    delivery_date = data.get('delivery_date')
    items = data.get('items')
    telephone = data.get('telephone')
    user_id = data.get('user_id')
    total_amount = str(sum(float(item['price']) * item['quantity'] for item in items))

    order_details = (
        f"Email: {email}\n"
        f"Телефон: {telephone}\n"
        f"Адрес: {address}\n"
        f"Дата доставки: {delivery_date}\n"
        f"Время доставки: {delivery_time}\n"
        f"Товары: {items}\n"
        f"Общая сумма: {total_amount}\n"
    )

    await message.answer(f"Пожалуйста, подтвердите ваш заказ:\n\n{order_details}", reply_markup=create_confirm_keyboard())
    await state.set_state(OrderForm.confirm_order)


@dp.callback_query(lambda c: c.data and c.data == 'confirm_yes')
async def process_order(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    email = data.get('email')
    address = data.get('address')
    delivery_date = data.get('delivery_date')
    delivery_time = data.get('delivery_time')
    items = data.get('items')
    telephone = data.get('telephone')
    user_id = data.get('user_id')
    total_amount = str(sum(total(item['price']) * item['quantity'] for item in items))

    order_data = {
        'user': user_id,
        'delivery_date': delivery_date,
        'delivery_time': delivery_time,
        'address': address,
        'contact': telephone,
        'total_amount': str(total_amount),
        'status': 'Заказан',
        'items': items
    }

    try:
        response = requests.post('http://127.0.0.1:8000/orders/api/orders/', json=order_data)
        response.raise_for_status()
        await bot.send_message(callback_query.from_user.id, "Ваш заказ был успешно оформлен!")
    except requests.RequestException as e:
        await bot.send_message(callback_query.from_user.id, f"Не удалось оформить заказ: {e}")
        logger.error(f"Failed to create order: {e}")

    await state.clear()


@dp.callback_query(lambda c: c.data and c.data == 'confirm_no')
async def cancel_order(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Ваш заказ был отменен.")
    await state.clear()



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
