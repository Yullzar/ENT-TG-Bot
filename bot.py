import telebot
from telebot import types


BOT_TOKEN = '8289594090:AAF5_oPZuw7MAYsQ5lWBnPoBGaQqRZGrV0o'
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_subjects = types.KeyboardButton('📚 Предметы')
    btn_practice = types.KeyboardButton('📝 Пробный ент')
    btn_stats = types.KeyboardButton('📊 Статистика')
    btn_help = types.KeyboardButton('❓ Помощь')
    
    markup.add(btn_subjects, btn_practice, btn_stats, btn_help)
    
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в бота для подготовки к ЕНТ! 🎓\n\n"
        "Выберите действие:",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "🤖 *Помощь по боту*\n\n"
        "Этот бот поможет вам подготовиться к ЕНТ.\n\n"
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/help - Справка\n\n"

    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    bot.send_message(
        message.chat.id,
        "📊 *Ваша статистика*\n\n",
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['subjects'])
def subjects_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_math = types.KeyboardButton('📐 Математика')
    btn_physics = types.KeyboardButton('⚛️ Физика')
    btn_chemistry = types.KeyboardButton('🧪 Химия')
    btn_biology = types.KeyboardButton('🧬 Биология')
    btn_history = types.KeyboardButton('📜 История Казахстана')
    btn_world_history = types.KeyboardButton('🌍 Всемирная история')
    btn_english = types.KeyboardButton('🇬🇧 Английский')
    btn_kazakh = types.KeyboardButton('🇰🇿 Казахский')
    btn_russian = types.KeyboardButton('🇷🇺 Русский')
    btn_literature = types.KeyboardButton('📖 Литература')
    btn_geography = types.KeyboardButton('🌍 География')
    btn_law = types.KeyboardButton('⚖️ Право')
    btn_back = types.KeyboardButton('🔙 Назад')
    
    markup.add(btn_math, btn_physics, btn_chemistry, btn_biology,
               btn_history, btn_world_history, btn_english, btn_kazakh,
               btn_russian, btn_literature, btn_geography, btn_law, btn_back)
    
    bot.send_message(
        message.chat.id,
        "Выберите предмет для подготовки:",
        reply_markup=markup
    )


@bot.message_handler(commands=['probent'])
def prob_ent_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_mir_pravo = types.KeyboardButton('Всемирная история - Основы Права')
    btn_fiz_mat = types.KeyboardButton('Математика - Физика')
    btn_geo_mat = types.KeyboardButton('Математика - География')
    btn_him_fiz = types.KeyboardButton('Химия - Физика')
    btn_bio_him = types.KeyboardButton('Биология - Химия')
    btn_bio_geo = types.KeyboardButton('Биология - География')
    btn_geo_eng = types.KeyboardButton('География - Английский язык')
    btn_mir_geo = types.KeyboardButton('Всемирная история - География')
    btn_eng_mir = types.KeyboardButton('Английский язык - Всемирная история')
    btn_kaz_kaz = types.KeyboardButton('Казахский язык - Казахская литература')
    btn_rus_rus = types.KeyboardButton('Русский язык - Русскаая литература')
    btn_mat_info= types.KeyboardButton('Математика - Информатика')
    btn_back = types.KeyboardButton('🔙 Назад')
    markup.add(btn_mir_pravo, btn_fiz_mat, btn_geo_mat, btn_him_fiz, btn_bio_him, btn_bio_geo, btn_geo_eng, btn_mir_geo, btn_eng_mir, btn_kaz_kaz, btn_rus_rus, btn_mat_info, btn_back)

    bot.send_message(
        message.chat.id,
        "📝 *Пробный ЕНТ*\n\nВыберите профильные предметы:",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def text_handler(message):
    if message.text == '📚 Предметы':
        subjects_command(message)
    elif message.text == '📝 Пробный ент':
        prob_ent_menu(message)
    elif message.text == '📊 Статистика':
        stats_command(message)
    elif message.text == '❓ Помощь':
        help_command(message)
    elif message.text == '🔙 Назад':
        start_command(message)
    elif message.text in [
    '📐 Математика', '⚛️ Физика', '🧪 Химия', '🧬 Биология',
    '📜 История Казахстана', '🌍 Всемирная история', '🇬🇧 Английский',
    '🇰🇿 Казахский', '🇷🇺 Русский', '📖 Литература', '🌍 География', '⚖️ Право'
    ]:
        subject_selected(message)
    else:
        bot.send_message(
            message.chat.id,
            "Используйте меню для навигации или введите /start для возврата в главное меню."
        )


def subject_selected(message):
    subject = message.text
    bot.send_message(
        message.chat.id,
        f"Вы выбрали: {subject}\n\n",
        parse_mode='Markdown'
    )

if __name__ =='__main__':
    print("Бот запущен...")
    bot.polling()
