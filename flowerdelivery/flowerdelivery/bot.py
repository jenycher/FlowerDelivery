import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
import requests
import json
from settings import BOT_TOKEN

TOKEN = BOT_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class OrderForm(StatesGroup):
    email = State()
    bouquet = State()
    address = State()
    delivery_date = State()


def is_user_registered(email):
    response = requests.get(f'http://127.0.0.1:8000/api/users/', params={'email': email})
    return response.status_code == 200 and response.json().get('exists', False)


@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.answer(
        "Приветствую в FlowerDelivery Bot! Пожалуйста, введите вашу электронную почту для проверки регистрации.")
    await state.set_state(OrderForm.email)


@dp.message(OrderForm.email)
async def get_email(message: types.Message, state: FSMContext):
    email = message.text
    if not is_user_registered(email):
        await message.answer(
            "Вы не зарегистрированы на нашем сайте. Пожалуйста, зарегистрируйтесь на сайте перед тем, как сделать заказ.")
        await state.finish()
        return

    await state.update_data(email=email)
    await message.answer("Проверка прошла успешно! Теперь введите название букета для заказа:")
    await state.set_state(OrderForm.bouquet)


@dp.message(OrderForm.bouquet)
async def get_bouquet(message: types.Message, state: FSMContext):
    await state.update_data(bouquet=message.text)
    await message.answer("Пожалуйста, введите ваш адрес доставки:")
    await state.set_state(OrderForm.address)


@dp.message(OrderForm.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Пожалуйста, введите дату доставки (YYYY-MM-DD):")
    await state.set_state(OrderForm.delivery_date)


@dp.message(OrderForm.delivery_date)
async def get_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bouquet = data['bouquet']
    address = data['address']
    delivery_date = message.text
    email = data['email']

    # Send order to Django API
    order_data = {
        "email": email,
        "bouquet": bouquet,
        "delivery_address": address,
        "delivery_date": delivery_date,
        "status": "pending"
    }

    response = requests.post('http://127.0.0.1:8000/api/orders/', data=json.dumps(order_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        await message.reply("Ваш заказ был успешно оформлен!")
    else:
        await message.reply("Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте снова.")

    await state.finish()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
