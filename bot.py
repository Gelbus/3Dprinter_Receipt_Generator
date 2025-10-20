import asyncio
import os
import re
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.utils.markdown import code

from receipt_generator import Receipt
import config


# === Настройки ===
BOT_TOKEN = config.BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

receipt = Receipt()


# === FSM (состояния) ===
class OrderState(StatesGroup):
    waiting_for_order = State()
    waiting_for_files = State()

# === Глобальное хранение задач обновления ===
pending_updates = defaultdict(lambda: None)

# === Клавиатуры ===
def get_done_keyboard():
    kb = [
        [InlineKeyboardButton(text="Завершить загрузку", callback_data="done_uploading")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="Создать новый заказ")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

# === Проверка формата сообщения ===
# def parse_order(text: str):
#     lines = text.strip().split('\n')
#     items = []
#     for line in lines:
#         match = re.match(r'^([a-zA-Zа-яА-ЯёЁ0-9_-]+)\s+(\d+)$', line.strip())
#         if not match:
#             return None
#         name, count = match.groups()
#         items.append((name, int(count)))
#     return items
def parse_order(text: str):
    lines = text.strip().split('\n')
    items = []
    for line in lines:
        line = line.strip()
        # Ищем последнее слово, состоящее только из цифр, в конце строки
        match = re.match(r'^(.+?)\s+(\d+)$', line)
        if not match:
            return None
        name, count = match.groups()
        items.append((name.strip(), int(count)))
    return items

# === Функция обновления кнопки с задержкой и удалением старого сообщения ===
async def delayed_update_button(chat_id, state: FSMContext):
    global pending_updates

    if pending_updates[chat_id]:
        pending_updates[chat_id].cancel()

    async def update():
        await asyncio.sleep(1.5)  # Ждем 1.5 секунды после последнего файла
        user_data = await state.get_data()
        done_msg_id = user_data.get('done_msg_id')

        # Удаляем старое сообщение с кнопкой
        if done_msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=done_msg_id)
            except Exception:
                pass  # Сообщение могло быть удалено вручную

        # Отправляем новое сообщение с кнопкой
        msg = await bot.send_message(chat_id=chat_id, text="Когда загрузите все файлы, нажмите кнопку ниже.", reply_markup=get_done_keyboard())
        await state.update_data(done_msg_id=msg.message_id)
        pending_updates[chat_id] = None

    task = asyncio.create_task(update())
    pending_updates[chat_id] = task

# === Обработчик команды /start ===
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Введите список имен деталей без расширения в формате:\n"
        "ИмяДеталь1 количество\n"
        "ИмяДеталь2 количество\n"
        "..."
    )
    await state.set_state(OrderState.waiting_for_order)

# === Обработка сообщения с заказом ===
@dp.message(OrderState.waiting_for_order)
async def process_order(message: Message, state: FSMContext):
    text = message.text
    items = parse_order(text)

    if items is None:
        await message.answer(
            "Неверный формат. Пожалуйста, введите снова.",
            reply_markup=get_main_keyboard()
        )
        return

    names = [item[0] for item in items]
    await state.update_data(order_text=text, required_files=names, received_files=[])
    await message.answer(f"Принято\\. Теперь загрузите файлы:\n{code('\n'.join(names))}", parse_mode="MarkdownV2")
    msg = await message.answer("Когда загрузите все файлы, нажмите кнопку ниже.", reply_markup=get_done_keyboard())
    await state.update_data(done_msg_id=msg.message_id)
    await state.set_state(OrderState.waiting_for_files)

# === Обработка загрузки файлов ===
@dp.message(OrderState.waiting_for_files, F.document)
async def handle_document(message: Message, state: FSMContext):
    user_data = await state.get_data()
    required_files = set(user_data['required_files'])
    received_files = user_data.get('received_files', [])
    file_info = message.document
    file_name = file_info.file_name

    # Проверка расширения
    if not file_name.lower().endswith('.stl'):
        await message.answer(f"Файл {file_name} не является STL. Пропущен.")
        return

    # Сохранение файла
    file_path = os.path.join('data', 'stl', file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    file = await bot.get_file(file_info.file_id)
    await bot.download_file(file.file_path, file_path)

    received_files.append(file_name)
    await state.update_data(received_files=received_files)

    uploaded_names = {os.path.splitext(f)[0] for f in received_files}
    missing = required_files - uploaded_names
    await message.answer(f"Файл {code(file_name)} загружен\\.\nОсталось:\n{code('\n'.join(missing) or 'все файлы загружены!')}", parse_mode="MarkdownV2")

    # Откладываем обновление кнопки (с удалением старого сообщения)
    await delayed_update_button(message.chat.id, state)

# === Обработка нажатия кнопки "Завершить загрузку" ===
@dp.callback_query(F.data == "done_uploading")
async def process_done_uploading(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    required_files = set(user_data['required_files'])
    received_files = user_data.get('received_files', [])
    uploaded_names = {os.path.splitext(f)[0] for f in received_files}

    missing = required_files - uploaded_names
    extra = uploaded_names - required_files

    if missing:
        done_msg_id = user_data.get('done_msg_id')
        if done_msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=done_msg_id)
            except Exception:
                pass
        msg = await callback.message.answer(f"Не загружены:\n{code('\n'.join(missing))}", reply_markup=get_done_keyboard(), parse_mode="MarkdownV2")
        await state.update_data(done_msg_id=msg.message_id)
        await callback.answer()
        return
    if extra:
        done_msg_id = user_data.get('done_msg_id')
        if done_msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=done_msg_id)
            except Exception:
                pass
        msg = await callback.message.answer(f"Лишние файлы: {', '.join(extra)}.", reply_markup=get_done_keyboard())
        await state.update_data(done_msg_id=msg.message_id)
        await callback.answer()
        return

    order_text = user_data['order_text']
    # Вызов вашей функции
    receipt.set_data(order_text)
    receipt.generate_report()
    # MyFUNC(order_text)

    # Удаляем сообщение с кнопкой "Завершить загрузку"
    done_msg_id = user_data.get('done_msg_id')
    if done_msg_id:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=done_msg_id)
        except Exception:
            pass

    # Отправка PDF пользователю
    pdf_path = os.path.join('data', 'reports', 'output2.pdf')  # замените на реальное имя файла
    if os.path.exists(pdf_path):
        await callback.message.answer_document(types.FSInputFile(pdf_path))
    else:
        await callback.message.answer("Ошибка: PDF не был сгенерирован.")

    await state.clear()
    await callback.message.answer("Готово!", reply_markup=get_main_keyboard())
    await callback.answer()

# === Обработка команды "Создать новый заказ" (обычная кнопка) ===
@dp.message(F.text == "Создать новый заказ")
async def reset_process(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Процесс сброшен. Введите список деталей:",
        reply_markup=get_main_keyboard()
    )
    await state.set_state(OrderState.waiting_for_order)

# === Обработка не-документов в состоянии загрузки файлов ===
@dp.message(OrderState.waiting_for_files)
async def handle_non_doc(message: Message, state: FSMContext):
    user_data = await state.get_data()
    done_msg_id = user_data.get('done_msg_id')

    # Удаляем старое сообщение с кнопкой, если есть
    if done_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=done_msg_id)
        except Exception:
            pass

    # Отправляем новое сообщение с кнопкой
    msg = await message.answer("Пожалуйста, загрузите файлы или нажмите кнопку завершения.", reply_markup=get_done_keyboard())
    await state.update_data(done_msg_id=msg.message_id)


if __name__ == '__main__':
    dp.run_polling(bot)