import telebot
from telebot import types
import csv
import random

BOT_TOKEN = '8289594090:AAF5_oPZuw7MAYsQ5lWBnPoBGaQqRZGrV0o'
bot = telebot.TeleBot(BOT_TOKEN)

SUBJECT_FILES = {
    '📐 Математика': 'questions/math_literacy.csv',
    '⚛️ Физика': 'questions/physics.csv',
    '🧪 Химия': 'questions/chemistry.csv',
    '🧬 Биология': 'questions/biology.csv',
    '📜 История Казахстана': 'questions/kazakhstan_history.csv',
    '🌍 Всемирная история': 'questions/world_history.csv',
    '🇬🇧 Английский': 'questions/english.csv',
    '🇰🇿 Казахский': 'questions/kazakh.csv',
    '🇷🇺 Русский': 'questions/russian.csv',
    '📖 Литература': 'questions/russian_lit.csv',
    '🌍 География': 'questions/geography.csv',
    '⚖️ Право': 'questions/law.csv'
}

user_sessions = {}

def load_questions(subject_file):
    questions = []
    try:
        with open(subject_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                questions.append(row)
    except Exception as e:
        print(f"Error loading {subject_file}: {e}")
    return questions

def get_random_questions(questions, count=3):
    if len(questions) <= count:
        return questions
    return random.sample(questions, count)


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
    subject_file = SUBJECT_FILES.get(subject)
    
    if not subject_file:
        bot.send_message(message.chat.id, "Ошибка: предмет не найден")
        return
    questions = load_questions(subject_file)
    if not questions:
        bot.send_message(message.chat.id, "Вопросы для этого предмета пока не добавлены")
        return
    
    #3 рандомных вопроса 
    selected_questions = get_random_questions(questions, 3)

    user_sessions[message.chat.id] = {
        'subject': subject,
        'questions': selected_questions,
        'current_index': 0,
        'correct_answers': 0
    }
    
    send_question(message.chat.id)

def send_question(chat_id):
    session = user_sessions.get(chat_id)
    if not session:
        return
    
    if session['current_index'] >= len(session['questions']):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn_back = types.KeyboardButton('🔙 Назад')
        markup.add(btn_back)
        bot.send_message(
            chat_id,
            f"✅ Тест завершен!\n\nПравильных ответов: {session['correct_answers']} из {len(session['questions'])}",
            reply_markup=markup
        )
        del user_sessions[chat_id]
        return
    
    question = session['questions'][session['current_index']]
    question_num = session['current_index'] + 1
    total_questions = len(session['questions'])
    
    message_text = f"{session['subject']} | {question['topic']}\n"
    message_text += f"Вопрос {question_num}/{total_questions}\n\n"
    message_text += f"{question['question']}\n\n"
    message_text += f"A) {question['a']}\n"
    message_text += f"B) {question['b']}\n"
    message_text += f"C) {question['c']}\n"
    message_text += f"D) {question['d']}"
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn_a = types.InlineKeyboardButton('A', callback_data='answer_a')
    btn_b = types.InlineKeyboardButton('B', callback_data='answer_b')
    btn_c = types.InlineKeyboardButton('C', callback_data='answer_c')
    btn_d = types.InlineKeyboardButton('D', callback_data='answer_d')
    btn_finish = types.InlineKeyboardButton('🛑 Завершить', callback_data='finish')
    
    markup.add(btn_a, btn_b, btn_c, btn_d)
    markup.add(btn_finish)
    
    bot.send_message(chat_id, message_text, reply_markup=markup)

@bot.callback_query_handler()
def callback_handler(call):
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        bot.answer_callback_query(call.id, "Сессия не найдена")
        return
    
    if call.data == 'finish':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn_back = types.KeyboardButton('🔙 Назад')
        markup.add(btn_back)
        bot.send_message(
            chat_id,
            f"🛑 Тест завершен досрочно!\n\nПравильных ответов: {session['correct_answers']} из {len(session['questions'])}",
            reply_markup=markup
        )
        del user_sessions[chat_id]
        bot.answer_callback_query(call.id)
        return
    
    if call.data == 'next':
        bot.delete_message(chat_id, call.message.message_id)
        send_question(chat_id)
        return
    
    if call.data.startswith('answer_'):
        user_answer = call.data.split('_')[1].upper()
        current_question = session['questions'][session['current_index']]
        correct_answer = current_question['correct'].upper()
        

        if user_answer == correct_answer:
            session['correct_answers'] += 1
            result_text = "✅ Правильно!"
        else:
            result_text = f"❌ Неправильно! \nПравильный ответ: {correct_answer}"
        
        original_text = call.message.text
        new_text = original_text + f"\n\n{result_text}"
        
        markup = types.InlineKeyboardMarkup()
        btn_next = types.InlineKeyboardButton('➡️ Следующий вопрос', callback_data='next')
        btn_finish = types.InlineKeyboardButton('🛑 Завершить', callback_data='finish')
        markup.add(btn_next)
        markup.add(btn_finish)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=new_text,
            reply_markup=markup
        )
        
        session['current_index'] += 1
        bot.answer_callback_query(call.id)
        return
    
    bot.answer_callback_query(call.id)

if __name__ =='__main__':
    print("Бот запущен...")
    bot.polling()
