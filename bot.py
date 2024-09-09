from telethon import TelegramClient, events, Button
import random

# Настройки бота
bot_token = '7453960039:AAG5x4YxOz3IRrn5xPPkY7Qa2-DoIU7s9Ms'
api_id = '18778182'
api_hash = 'f5adaf2bbb96d97ff4443fdc0c4ddb38'
admin_ids = {5722874142, 1681831330, 7007999791}

client = TelegramClient('feedback_bot', api_id, api_hash).start(bot_token=bot_token)

# Определение переменных
user_states = {}
responding_users = {}
message_ids = {}
blocked_users = set()
blocked_users_notified = set()

def generate_unique_id():
    """Генерация уникального номера."""
    return random.randint(99999, 999999999)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id in blocked_users:
        if event.sender_id not in blocked_users_notified:
            await event.respond("❌ Ви заблоковані і не можете користуватися ботом.")
            blocked_users_notified.add(event.sender_id)
        return
    await event.respond(
        "🕵️Ласкаво просимо в бота зворотнього зв'язку\n\n"
        "✏️Якщо ви хочете нам написати, натисніть: «НАПИСАТИ💬»",
        buttons=[Button.inline('НАПИСАТИ💬', 'НАПИСАТИ')]
    )

@client.on(events.CallbackQuery)
async def handle_query(event):
    data = event.data.decode('utf-8')

    if event.sender_id in blocked_users:
        if event.sender_id not in blocked_users_notified:
            await event.respond("❌ Ви заблоковані і не можете користуватися ботом.")
            blocked_users_notified.add(event.sender_id)
        return

    # Получаем сообщение из события
    message = await event.get_message()

    if data == 'НАПИСАТИ':
        user_states[event.sender_id] = 'awaiting_feedback'
        await event.respond(
            "Напишіть свій запит до адміністрації каналу «Назва каналу».\n\n"
            "⌛Найближчі 24 години ваше повідомлення буде розглянуто!"
        )
        await message.delete()  # Удаление сообщения с кнопками
    elif data == 'Головне_меню':
        await event.respond(
            "🕵️Ласкаво просимо в бота зворотнього зв'язку «Назва каналу»\n\n"
            "✏️Якщо ви хочете нам написати, натисніть: «НАПИСАТИ💬»",
            buttons=[Button.inline('НАПИСАТИ💬', 'НАПИСАТИ')]
        )
        await message.delete()  # Удаление сообщения с кнопками
    elif data.startswith('ВІДПОВІСТИ'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_respond = int(parts[1])
            user_states[event.sender_id] = 'awaiting_message'
            responding_users[event.sender_id] = user_id_to_respond
            await event.respond("Напишіть повідомлення для користувача нижче:",
                                buttons=[Button.inline('ЗАВЕРШИТИ', f'ЗАВЕРШИТИ_{event.sender_id}')])
            try:
                await client.send_message(user_id_to_respond, 
                                          "👁️Ваше повідомлення вже розглядають!\n⚡Очікуйте відповіді!")
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id_to_respond}: {e}")
    elif data.startswith('ЗАВЕРШИТИ'):
        parts = data.split('_')
        if len(parts) > 1:
            admin_id = int(parts[1])
            if admin_id in responding_users:
                user_id_to_respond = responding_users.pop(admin_id, None)
                if user_id_to_respond:
                    await client.send_message(user_id_to_respond, "__```🚫Адміністрація покинула розмову🚫```__\n\n**🙈Якщо будемо ще корисні, звертайтеся**")
                    await event.respond("🛑Відповідь завершено. Ви можете тепер виконати інші дії.")
                    await message.delete()  # Удаление сообщения с кнопками
    elif data.startswith('BLOCK'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_block = int(parts[1])
            blocked_users.add(user_id_to_block)
            blocked_users_notified.add(user_id_to_block)
            await client.send_message(user_id_to_block, "**__🔒Ви були заблоковані адміністрацією.__**")
            await event.respond("✅Користувача заблоковано!")
    elif data.startswith('UNBLOCK'):
        parts = data.split('_')
        if len(parts) > 1:
            user_id_to_unblock = int(parts[1])
            if user_id_to_unblock in blocked_users:
                blocked_users.remove(user_id_to_unblock)
                blocked_users_notified.discard(user_id_to_unblock)
                await event.respond("✅Користувача розблоковано!")
                await client.send_message(user_id_to_unblock, "**🟢Ви були розблоковані адміністратором.**")
            else:
                await event.respond("```❌Користувач не був заблокований.```")

@client.on(events.NewMessage)
async def handle_user_message(event):
    if event.is_private and event.sender_id not in admin_ids:
        if event.sender_id in blocked_users:
            if event.sender_id not in blocked_users_notified:
                await event.respond("❌ Ви заблоковані і не можете надсилати повідомлення.")
                blocked_users_notified.add(event.sender_id)
            return

        # Обработка голосовых сообщений, фото, видео и файлов
        if event.voice or event.photo or event.video or event.file:
            await event.respond(
                "**❌Нажаль ми не приймаємо повідомлення в цих форматах:** "
                "**Голосові повідомлення/Фото/Відео/Файли.**\n\n"
                "__🫶Якщо виникнуть питання або пропозиції, опишіть їх краще в текстовому форматі і ми вам відповімо як умога швидше!__",
               buttons=[
            [Button.inline('НАПИСАТИ 💬', 'НАПИСАТИ')],  # Кнопка сверху
            [Button.inline('ГОЛОВНЕ МЕНЮ', 'Головне_меню')]  # Кнопка снизу
        ]
    )
            return

        state = user_states.get(event.sender_id)
        if state == 'awaiting_feedback':
            unique_id = generate_unique_id()
            message_ids[event.sender_id] = unique_id

            await event.respond(
                "Дякуємо за повідомлення, скоро його розглянемо.\n\n"
                "🧐Якщо це не все, що ви хочете написати, надішліть все одним повідомленням. Як відправити ще одне повідомлення?\n```Головне меню > НАПИСАТИ💬 > Ваше повідомлення```",
                buttons=[Button.inline('Головне меню', 'Головне_меню')]
            )

            sender = await event.get_sender()
            first_name = sender.first_name if sender.first_name else "Без имени"
            last_name = sender.last_name if sender.last_name else ""
            full_name = f"{first_name} {last_name}".strip()
            username = f"@{sender.username}" if sender.username else "Немає"

            unique_number = message_ids.get(event.sender_id, generate_unique_id())
            message_to_admin = (
                "📥Нове повідомлення\n"
                f"👤Від користувача: {full_name}\n"
                f"🔢UserID: tg://openmessage?user_id={event.sender_id}\n"
                f"🕵️Username:{username}\n"
                f"♻️Унікальний номер: #id{unique_number}\n\n"
                f"📥Повідомлення:\n```{event.message.text}```"
            )

            for admin_id in admin_ids:
                try:
                    await client.send_message(
                        admin_id,
                        message_to_admin,
                        buttons=[
                            Button.inline('ВІДПОВІСТИ', f'ВІДПОВІСТИ_{event.sender_id}'),
                            Button.inline('⛔ ЗАБЛОКУВАТИ⛔', f'BLOCK_{event.sender_id}'),
                            Button.inline('🟢РОЗБЛОКОВАТИ 🟢', f'UNBLOCK_{event.sender_id}')
                        ]
                    )
                except Exception as e:
                    print(f"Ошибка при отправке сообщения админу {admin_id}: {e}")

            user_states[event.sender_id] = 'none'

# Запуск бота
print("🔥СВЯЗЬ ЗАПУЩЕНА🔥")
client.run_until_disconnected()

