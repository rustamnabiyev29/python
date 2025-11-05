import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command

bot = Bot(token="8246247372:AAFRE-gWlN4DvQFCRsIyZCvly5dPBBG6Q1U")  # вставь свой токен от BotFather
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    # создаём две кнопки
    btn1 = KeyboardButton(text="Кнопка 1")
    btn2 = KeyboardButton(text="Кнопка 2")

    # создаём клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[btn1, btn2]],  # две кнопки в один ряд
        resize_keyboard=True
    )

    await message.answer("Выбери кнопку:", reply_markup=keyboard)


@dp.message()
async def button_handler(message: Message):
    if message.text == "Кнопка 1":
        await message.answer("Ты нажал кнопку 1!")
    elif message.text == "Кнопка 2":
        await message.answer("Ты нажал кнопку 2!")
    else:
        await message.answer("Я не знаю такой команды. Нажми кнопку 🙂")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
