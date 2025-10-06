import telebot
import time
import random

TOKEN = "8219415257:AAEjAb5dfVrs7Cw0O_-8RpQjXmbPNC0bOC0"
bot = telebot.TeleBot(TOKEN)

# ===== Настройки =====
BAD_WORDS = ["дурак", "идиот", "сука", "блядь", "тварь", "нахуй", "пидор", "еблан"]
SPAM_TRIGGERS = ["http", "t.me", "@", "скидки", "бесплатно"]

violations = {}  # {user_id: количество нарушений}
last_message_time = {}  # для антифлуда

# ===== Правила =====
rules_text = """
📜 Правила чата:
1️⃣ Оскорбления — мут на 1 день.
2️⃣ Спам / флуд — мут на 3 дня.
3️⃣ Частые нарушения — бан или вечный мут.
4️⃣ Повторные нарушения после разбана — жёсткие наказания.
"""

@bot.message_handler(commands=["start", "rules"])
def start(msg):
    bot.reply_to(msg, rules_text)


# ===== Проверка сообщений =====
@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_message(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    text = message.text.lower()
    now = time.time()

    # Проверка на флуд
    if user_id in last_message_time and now - last_message_time[user_id] < 2:
        handle_violation(message, "Флуд", 3)
        return
    last_message_time[user_id] = now

    # Проверка на плохие слова
    if any(word in text for word in BAD_WORDS):
        handle_violation(message, "Оскорбления", 1)
        return

    # Проверка на спам
    if any(trigger in text for trigger in SPAM_TRIGGERS):
        handle_violation(message, "Спам", 3)
        return


def handle_violation(message, reason, days):
    user_id = message.from_user.id
    username = message.from_user.first_name
    chat_id = message.chat.id

    # увеличиваем счётчик нарушений
    violations[user_id] = violations.get(user_id, 0) + 1
    count = violations[user_id]

    # шанс вечного мута (примерно 1 к 10)
    eternal_chance = random.randint(1, 10)

    # ===== Вечный мут =====
    if eternal_chance == 1 and count >= 2:
        bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        bot.reply_to(message, f"💀 {username}, получил вечный мут! Причина: {reason}")
        try:
            bot.send_message(user_id, f"🤐 Вы получили *вечный мут* в чате.\nПричина: {reason}\n"
                                      "💬 Обратитесь к администратору, если хотите апелляцию.")
        except:
            pass
        return

    # ===== Первое нарушение =====
    if count == 1:
        duration = days * 24 * 60 * 60
        bot.restrict_chat_member(chat_id, user_id, until_date=time.time() + duration, can_send_messages=False)
        bot.reply_to(message, f"⚠️ {username}, мут на {days} день за: {reason}")
    # ===== Второе =====
    elif count == 2:
        duration = 7 * 24 * 60 * 60
        bot.restrict_chat_member(chat_id, user_id, until_date=time.time() + duration, can_send_messages=False)
        bot.reply_to(message, f"🚨 {username}, повторное нарушение — мут на 7 дней.")
    # ===== Третье — вечный бан =====
    elif count >= 3:
        bot.ban_chat_member(chat_id, user_id)
        bot.send_message(chat_id, f"💣 {username} забанен навсегда за систематические нарушения.")
        # Уведомление в личку
        try:
            bot.send_message(user_id, f"🚫 Вас *забанили навсегда* в чате '{message.chat.title}'.\n"
                                      f"Причина: {reason}\n"
                                      "⛔ Апелляция невозможна.")
        except:
            pass


# ==== Команда для прощения (админам) ====
@bot.message_handler(commands=["forgive"])
def forgive_user(msg):
    """Админ может простить пользователя"""
    if not msg.reply_to_message:
        return bot.reply_to(msg, "Ответь на сообщение нарушителя командой /forgive")

    user_id = msg.reply_to_message.from_user.id
    username = msg.reply_to_message.from_user.first_name
    if user_id in violations:
        violations[user_id] = max(0, violations[user_id] - 1)
        bot.reply_to(msg, f"🙏 {username} прощён. Нарушения уменьшены.")
    else:
        bot.reply_to(msg, f"😇 {username} не имеет нарушений.")


# ==== Основной запуск ====
print("🛡 Бот-модератор запущен...")
while True:
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(3)