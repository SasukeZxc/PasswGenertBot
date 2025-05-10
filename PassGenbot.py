import logging
import random
import asyncio
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
import sqlite3
from datetime import datetime

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('ratings.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

BOT_TOKEN = 'YOUR-BOT-TOKEN'

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Локализация
TEXTS = {
    "ru": {
        "main_menu": "🌟 <b>Главное меню</b> 🌟\n\nВыберите действие:",
        "compliment_btn": "🤖 Сгенерировать пароль",
        "fact_btn": "🧠 Случайный факт",
        "rate_btn": "⭐ Оценить бота",
        "help_btn": "ℹ️ Помощь",
        "compliment_title": "🤖 Ваш пароль:",
        "fact_title": "🧠 <b>Интересный факт:</b>",
        "rate_title": "⭐ <b>Оцените бота:</b>",
        "thanks_rating": "🙏 <b>Спасибо за {stars} оценку!</b>",
        "help_text": (
            "ℹ️ <b>Помощь</b>\n\n"
            "Этот бот создан, чтобы поднимать настроение!\n\n"
            "• Нажмите <b>🤖 Сгенерировать пароль</b> для получения случайного пароля\n"
            "• Выберите <b>Случайный факт</b> для интересной информации\n"
            "• Оцените бота, если вам понравилось!\n"
            "• Средняя оценка бота: {average_rating:.1f} ⭐ (на основе {rating_count} оценок)\n"
            "• Бот защищен Apache License: https://www.apache.org/licenses/LICENSE-2.0\n"
            "• Создатель бота @Girlanda228"
        ),
        "back_btn": "🔙 Назад",
        "choose_language": "🌍 <b>Выберите язык:</b>",
        "language_select": "🇷🇺 Русский"
    },
    "en": {
        "main_menu": "🌟 <b>Main Menu</b> 🌟\n\nChoose an action:",
        "compliment_btn": "🤖 Generate password",
        "fact_btn": "🧠 Random fact",
        "rate_btn": "⭐ Rate bot",
        "help_btn": "ℹ️ Help",
        "compliment_title": "🤖 <b>Your password:</b>",
        "fact_title": "🧠 <b>Interesting fact:</b>",
        "rate_title": "⭐ <b>Rate the bot:</b>",
        "thanks_rating": "🙏 <b>Thank you for {stars} rating!</b>",
        "help_text": (
            "ℹ️ <b>Help</b>\n\n"
            "This bot was created to cheer you up!\n\n"
            "• Click <b>🤖 Generate password</b> to get a random password\n"
            "• Select <b>Random fact</b> for interesting information\n"
            "• Rate the bot if you liked it!\n"
            "• Average bot rating: {average_rating:.1f} ⭐ (based on {rating_count} ratings)\n"
            "• Bot protected by Apache License: https://www.apache.org/licenses/LICENSE-2.0\n"
            "• Bot creator @Girlanda228"
        ),
        "back_btn": "🔙 Back",
        "choose_language": "🌍 <b>Choose language:</b>",
        "language_select": "🇬🇧 English"
    }
}

# Списки сообщений
chars = '+-/*!&$#?=@<>abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

FACTS = {
    "ru": [
        "🦈 Акулы существуют дольше, чем деревья! (400 млн лет)",
        "🍯 Мёд никогда не портится – археологи находили съедобный мёд возрастом 3000 лет!",
        "🐧 Пингвины могут прыгать до 2 метров в высоту!",
        "🌙 На Луне есть запах... жареного мяса (по словам астронавтов)!",
        "🦷 Зубная эмаль — самая твердая ткань в организме!",
        "🐌 У улиток около 25 000 зубов!",
        "🕷️ Пауки могут ходить по воде благодаря поверхностному натяжению!",
        "🍌 Бананы — это ягоды, а клубника — нет!",
        "🦒 У жирафов и людей одинаковое количество шейных позвонков — 7!",
        "☕ Кофеин начинает действовать уже через 10 минут после употребления!",
        "🦴 Ребенок рождается с 270 костями, а у взрослого их всего 206!",
        "🐝 Пчелы общаются с помощью танца!",
        "🌊 Океаны содержат 99% жизненного пространства на Земле!",
        "🦇 Летучие мыши — единственные млекопитающие, способные к полету!",
        "📱 Смартфоны мощнее компьютеров, использовавшихся для полета на Луну!",
        "🦜 Попугаи могут жить дольше людей (некоторые виды — до 80 лет)!",
        "🍎 Яблоки плавают, потому что на 25% состоят из воздуха!",
        "🚀 Венера — единственная планета, вращающаяся против часовой стрелки!",
        "🦓 Зебры белые с черными полосками, а не наоборот!",
        "🧬 ДНК человека на 50% совпадает с ДНК банана!"
    ],
    "en": [
        "🦈 Sharks existed before trees! (400 million years)",
        "🍯 Honey never spoils - archaeologists found edible honey from 3000 years ago!",
        "🐧 Penguins can jump up to 6 feet high!",
        "🌙 The Moon smells like gunpowder (according to astronauts)!",
        "🦷 Tooth enamel is the hardest substance in the human body!",
        "🐌 Snails have about 25,000 teeth!",
        "🕷️ Some spiders can 'sail' across water using their legs as sails!",
        "🍌 Bananas are berries, but strawberries aren't!",
        "🦒 Giraffes and humans have the same number of neck vertebrae (7)!",
        "☕ Caffeine starts working within 10 minutes of consumption!",
        "🦴 Babies are born with 270 bones, adults have only 206!",
        "🐝 Honeybees communicate through 'waggle dances'!",
        "🌊 The ocean contains 99% of Earth's living space!",
        "🦇 Bats are the only mammals capable of sustained flight!",
        "📱 Your smartphone is millions of times more powerful than Apollo 11's computers!",
        "🦜 Some parrots can live over 80 years!",
        "🍎 Apples float because they're 25% air!",
        "🚀 Venus is the only planet that rotates clockwise!",
        "🦓 Zebras are white with black stripes, not black with white stripes!",
        "🧬 Humans share 50% of their DNA with bananas!"
    ]
}

# Разные изображения для каждого языка
MENU_PHOTOS = {
    "ru": "https://postimg.cc/2V2kKQrd",  # Замените на свою русскую версию
    "en": "https://postimg.cc/q6GJ0nnT"    # Замените на свою английскую версию
}

# Изображение для выбора языка
LANGUAGE_PHOTO = "https://postimg.cc/BXH7Hkrt"  # Замените на свое изображение

# Функции для работы с базой данных
def save_rating(user_id: int, rating: int):
    conn = sqlite3.connect('ratings.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO ratings (user_id, rating, timestamp) VALUES (?, ?, ?)',
        (user_id, rating, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_average_rating():
    conn = sqlite3.connect('ratings.db')
    cursor = conn.cursor()
    cursor.execute('SELECT AVG(rating), COUNT(*) FROM ratings')
    result = cursor.fetchone()
    conn.close()
    return result or (0, 0)  # (average, count)

async def send_main_menu(chat_id, context, edit_message_id=None, lang="ru"):
    """Отправка/обновление главного меню с картинкой на выбранном языке"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["compliment_btn"], callback_data=f"compliment_{lang}")],
        [InlineKeyboardButton(TEXTS[lang]["fact_btn"], callback_data=f"fact_{lang}")],
        [InlineKeyboardButton(TEXTS[lang]["rate_btn"], callback_data=f"rate_{lang}")],
        [InlineKeyboardButton(TEXTS[lang]["help_btn"], callback_data=f"help_{lang}")],
        [InlineKeyboardButton(TEXTS[lang]["language_select"], callback_data="change_language")]
    ])
    
    photo_url = MENU_PHOTOS[lang]
    
    if edit_message_id:
        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=edit_message_id,
            media=InputMediaPhoto(media=photo_url, caption=TEXTS[lang]["main_menu"], parse_mode='HTML'),
            reply_markup=keyboard
        )
    else:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=TEXTS[lang]["main_menu"],
            parse_mode='HTML',
            reply_markup=keyboard
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с выбором языка"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Клавиатура выбора языка
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")]
    ])
    
    await update.message.reply_photo(
        photo=LANGUAGE_PHOTO,
        caption=TEXTS["ru"]["choose_language"],
        parse_mode='HTML',
        reply_markup=keyboard
    )

#async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    """Обработчик нажатий inline-кнопок"""
#    query = update.callback_query
#    await query.answer()
#    
#    # Обработка смены языка
#    if query.data == "change_language":
#        keyboard = InlineKeyboardMarkup([
#            [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
#            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")]
#        ])
#        
#        current_lang = context.user_data.get("lang", "ru")
#        await query.edit_message_media(
#            media=InputMediaPhoto(
#                media=LANGUAGE_PHOTO,
#                caption=TEXTS[current_lang]["choose_language"],
#                parse_mode='HTML'
#            ),
#            reply_markup=keyboard
#        )
#        return
#    
#    # Обработка выбора языка
#    if query.data.startswith("set_lang_"):
#        lang = query.data.split("_")[-1]
#        context.user_data["lang"] = lang
#        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
#        return
#    
#    # Разделяем callback_data на действие и язык
#    if "_" in query.data:
#        action, lang = query.data.split("_", 1)
#    else:
#        action = query.data
#        lang = context.user_data.get("lang", "ru")
#    
#    if action == "compliment":
#
#        number = 1
#        #number = int(input('Количество паролей: '))
#        lenght = 8 #int(input("Длина пароля: "))
#        
#        for n in range(number):
#            password=''
#            for n in range(lenght):
#                password += random.choice(chars)
#        if query.message.photo:
#            await query.edit_message_caption(
#                caption=f"{TEXTS[lang]['compliment_title']}\n\n{password}",
#                parse_mode='HTML'
#            )
#        else:
#            await query.edit_message_text(
#                f"{TEXTS[lang]['compliment_title']}\n\n{password}",
#                parse_mode='HTML'
#            )
#        await asyncio.sleep(3)
#        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
#        
#    elif action == "fact":
#        fact = random.choice(FACTS[lang])
#        if query.message.photo:
#            await query.edit_message_caption(
#                caption=f"{TEXTS[lang]['fact_title']}\n\n{fact}",
#                parse_mode='HTML'
#            )
#        else:
#            await query.edit_message_text(
#                f"{TEXTS[lang]['fact_title']}\n\n{fact}",
#                parse_mode='HTML'
#            )
#        await asyncio.sleep(3)
#        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
#        
#    elif action == "rate":
#        await show_rating_menu(query, context, lang)
#        
#    elif action == "help":
#        if query.message.photo:
#            await query.edit_message_caption(
#                caption=TEXTS[lang]["help_text"],
#                parse_mode='HTML'
#            )
#        else:
#            await query.edit_message_text(
#                TEXTS[lang]["help_text"],
#                parse_mode='HTML'
#            )
#        await asyncio.sleep(5)
#        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
#
async def show_rating_menu(query, context, lang="ru"):
    """Показать меню оценки"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐", callback_data=f"rate1_{lang}"),
         InlineKeyboardButton("⭐⭐", callback_data=f"rate2_{lang}"),
         InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate3_{lang}")],
        [InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate4_{lang}"),
         InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate5_{lang}")],
        [InlineKeyboardButton(TEXTS[lang]["back_btn"], callback_data=f"back_{lang}")]
    ])
    
    if query.message.photo:
        await query.edit_message_caption(
            caption=TEXTS[lang]["rate_title"],
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        await query.edit_message_caption(
            TEXTS[lang]["rate_title"],
            parse_mode='HTML',
            reply_markup=keyboard
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    # Обработка смены языка
    if query.data == "change_language":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")]
        ])
        
        current_lang = context.user_data.get("lang", "ru")
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=LANGUAGE_PHOTO,
                caption=TEXTS[current_lang]["choose_language"],
                parse_mode='HTML'
            ),
            reply_markup=keyboard
        )
        return
    
    # Обработка выбора языка
    if query.data.startswith("set_lang_"):
        lang = query.data.split("_")[-1]
        context.user_data["lang"] = lang
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
        return
    
    # Разделяем callback_data на действие и язык
    if "_" in query.data:
        action, lang = query.data.split("_", 1)
    else:
        action = query.data
        lang = context.user_data.get("lang", "ru")
    
    if action == "compliment":
        # Запрашиваем у пользователя ввод количества и длины паролей
        await query.edit_message_caption(
            f"Введите количество и длину паролей в формате:\n\n<code>количество длина</code>\n\nНапример: <code>3 12</code>",
            parse_mode='HTML'
        )
        # Устанавливаем состояние ожидания ввода
        context.user_data['waiting_for_password_params'] = True
        context.user_data['lang'] = lang
        context.user_data['message_to_edit'] = query.message.message_id
        
    elif action == "fact":
        fact = random.choice(FACTS[lang])
        if query.message.photo:
            await query.edit_message_caption(
                caption=f"{TEXTS[lang]['fact_title']}\n\n{fact}",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_caption(
                f"{TEXTS[lang]['fact_title']}\n\n{fact}",
                parse_mode='HTML'
            )
        await asyncio.sleep(3)
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
        
    elif action == "rate":
        await show_rating_menu(query, context, lang)
        
    elif action == "help":
        if query.message.photo:
            await query.edit_message_caption(
                caption=TEXTS[lang]["help_text"],
                parse_mode='HTML'
            )
        else:
            await query.edit_message_caption(
                TEXTS[lang]["help_text"],
                parse_mode='HTML'
            )
        await asyncio.sleep(5)
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "change_language":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")]
        ])
        
        current_lang = context.user_data.get("lang", "ru")
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=LANGUAGE_PHOTO,
                caption=TEXTS[current_lang]["choose_language"],
                parse_mode='HTML'
            ),
            reply_markup=keyboard
        )
        return
    
    if query.data.startswith("set_lang_"):
        lang = query.data.split("_")[-1]
        context.user_data["lang"] = lang
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
        return
    
    if "_" in query.data:
        action, lang = query.data.split("_", 1)
    else:
        action = query.data
        lang = context.user_data.get("lang", "ru")
    
    if action == "compliment":
        # Удаляем предыдущее сообщение с меню
        try:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )
        except:
            pass
        
        # Отправляем новое сообщение с запросом параметров
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Введите количество и длину паролей в формате:\n\n<code>количество длина</code>\n\nНапример: <code>3 12</code>",
            parse_mode='HTML'
        )
        
        # Устанавливаем состояние ожидания ввода
        context.user_data['waiting_for_password_params'] = True
        context.user_data['lang'] = lang
        
    elif action == "fact":
        fact = random.choice(FACTS[lang])
        if query.message.photo:
            await query.edit_message_caption(
                caption=f"{TEXTS[lang]['fact_title']}\n\n{fact}",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                f"{TEXTS[lang]['fact_title']}\n\n{fact}",
                parse_mode='HTML'
            )
        await asyncio.sleep(3)
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
        
    elif action == "rate":
        await show_rating_menu(query, context, lang)
        
    elif action == "help":
        # Получаем среднюю оценку
        average_rating, rating_count = get_average_rating()
        
        if query.message.photo:
            await query.edit_message_caption(
                caption=TEXTS[lang]["help_text"].format(
                    average_rating=average_rating,
                    rating_count=rating_count
                ),
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                TEXTS[lang]["help_text"].format(
                    average_rating=average_rating,
                    rating_count=rating_count
                ),
                parse_mode='HTML'
            )
        await asyncio.sleep(5)
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстового ввода для параметров пароля"""
    if 'waiting_for_password_params' in context.user_data and context.user_data['waiting_for_password_params']:
        try:
            parts = update.message.text.split()
            if len(parts) != 2:
                raise ValueError
            
            number = int(parts[0])
            length = int(parts[1])
            
            # Проверяем допустимые значения
            if number <= 0 or length <= 0:
                raise ValueError
            if number > 20:
                await update.message.reply_text("Максимальное количество паролей - 20")
                return
            if length > 50:
                await update.message.reply_text("Максимальная длина пароля - 50 символов")
                return
                
            lang = context.user_data.get('lang', 'ru')
            
            # Генерируем пароли
            passwords = []
            for _ in range(number):
                password = ''.join([random.choice(chars) for _ in range(length)])
                passwords.append(password)
            
            result_text = f"{TEXTS[lang]['compliment_title']}\n\n" + "\n".join(passwords)
            
            # Отправляем результат
            await update.message.reply_text(
                result_text,
                parse_mode=None
            )
            
            await asyncio.sleep(1)
            await send_main_menu(update.effective_chat.id, context)
            
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите два положительных числа в формате:\nколичество длина\n\nНапример: 3 12",
                parse_mode=None
            )
            return
        finally:
            context.user_data.pop('waiting_for_password_params', None)
    else:
        await send_main_menu(update.effective_chat.id, context)

async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка оценки"""
    query = update.callback_query
    await query.answer()
    
    # Получаем язык и оценку
    if "_" in query.data:
        rating_part, lang = query.data.rsplit("_", 1)
    else:
        rating_part = query.data
        lang = context.user_data.get("lang", "ru")
    
    if rating_part.startswith("rate"):
        stars = int(rating_part.replace("rate", ""))
        star_icons = "⭐" * stars
        
        # Сохраняем оценку в базу данных
        save_rating(query.from_user.id, stars)
        
        if query.message.photo:
            await query.edit_message_caption(
                caption=TEXTS[lang]["thanks_rating"].format(stars=star_icons),
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                TEXTS[lang]["thanks_rating"].format(stars=star_icons),
                parse_mode='HTML'
            )
        await asyncio.sleep(2)
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
    elif rating_part == "back":
        await send_main_menu(query.message.chat_id, context, query.message.message_id, lang)
#def main() -> None:
#    """Запуск бота"""
#    application = Application.builder().token(BOT_TOKEN).build()
#
#    # Регистрация обработчиков
#    application.add_handler(CommandHandler("start", start))
#    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(set_lang_|compliment_|fact_|rate_|help_|back_|change_language)"))
#    application.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate[1-5]_"))
#    
#    # Обработчик текстовых сообщений
#    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
#                                        lambda u, c: send_main_menu(u.effective_chat.id, c)))
#
#    application.run_polling(allowed_updates=Update.ALL_TYPES)
#
#if __name__ == "__main__":
#    main()

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(set_lang_|compliment_|fact_|rate_|help_|back_|change_language)"))
    application.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate[1-5]_"))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()