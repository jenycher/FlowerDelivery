import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils import executor
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
    bouquet = State()
    address = State()
    delivery_date = State()


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Welcome to FlowerDelivery Bot! To place an order, type /order")


@dp.message(Command("order"))
async def place_order(message: types.Message):
    await message.reply("Please enter the bouquet name:")
    await OrderForm.bouquet.set()


@dp.message(OrderForm.bouquet)
async def get_bouquet(message: types.Message, state: FSMContext):
    await state.update_data(bouquet=message.text)
    await message.reply("Please enter your delivery address:")
    await OrderForm.address.set()


@dp.message(OrderForm.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.reply("Please enter the delivery date (YYYY-MM-DD):")
    await OrderForm.delivery_date.set()


@dp.message(OrderForm.delivery_date)
async def get_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bouquet = data['bouquet']
    address = data['address']
    delivery_date = data['delivery_date']
    user = message.from_user.username

    # Send order to Django API
    order_data = {
        "user": user,
        "bouquet": bouquet,
        "delivery_address": address,
        "delivery_date": delivery_date,
        "status": "pending"
    }

    response = requests.post('http://127.0.0.1:8000/api/orders/', data=json.dumps(order_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code == 201:
        await message.reply("Your order has been placed successfully!")
    else:
        await message.reply("There was an error placing your order. Please try again.")

    await state.clear()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
