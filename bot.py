import telebot
from telebot import types
import json
import random
import os

BOT_TOKEN = '8289594090:AAF5_oPZuw7MAYsQ5lWBnPoBGaQqRZGrV0o'
bot = telebot.TeleBot(BOT_TOKEN)

SUBJECT_FILES = {
    '📐 Математика': 'questions_json/Математика.json',
    '💻 Информатика': 'questions_json/Информатика.json',
    '🌍 Всемирная история': 'questions_json/Всемирная_история.json',
    '⚖️ Основы права': 'questions_json/Основы_права.json',
    '🧪 Химия': 'questions_json/Химия.json',
    '⚛️ Физика': 'questions_json/Физика.json',
    '🧬 Биология': 'questions_json/Биология.json',
    '🌍 География': 'questions_json/География.json',
    '🇬🇧 Английский язык': 'questions_json/Английский_язык.json',
    '🇰🇿 Казахский язык': 'questions_json/Казахский_язык.json',
    '🇰🇿 Казахская литература': 'questions_json/Казахская_литература.json',
    '🇷🇺 Русский язык': 'questions_json/Русский_язык.json',
    '🇷🇺 Русская литература': 'questions_json/Русская_литература.json',
    '📜 История Казахстана': 'questions_json/История_Казахстана.json',
    '📊 Математическая грамотность': 'questions_json/Математическая_грамотность.json',
    '📖 Грамотность чтения': 'questions_json/Грамотность_чтения.json'
}

user_sessions = {}

def load_questions(subject_file):
    questions = []
    try:
        with open(subject_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            subject_name = list(data.keys())[0]
            questions_data = data[subject_name]['questions']
            
            for q_id, q_data in questions_data.items():
                question = {
                    'topic': subject_name,
                    'question_text': q_data.get('questionText', ''),
                    'question_images': q_data.get('questionImages', []),
                    'answers': [],
                    'correct': q_data.get('correctLetter', '').replace(')', '').strip()
                }
                
                # Handle answers
                if 'answers' in q_data:
                    for ans in q_data['answers']:
                        answer = {
                            'letter': ans.get('letter', '').replace(')', '').strip(),
                            'text': ans.get('text', ''),
                            'images': ans.get('images', [])
                        }
                        question['answers'].append(answer)
                
                questions.append(question)
    except Exception as e:
        print(f"Error loading {subject_file}: {e}")
    return questions

def get_random_questions(questions, count=5):
    if len(questions) <= count:
        return questions
    return random.sample(questions, count)

def render_question(chat_id, session, question_num, total_questions):
    question = session['questions'][session['current_index']]
    user_messages = []
    
    question_has_images = len(question.get('question_images', [])) > 0
    
    for ans in question['answers']:
        if len(ans.get('images', [])) > 0:
            all_text_answers = False
            break
    else:
        all_text_answers = True
    
    header = f"{session['subject']} | {question.get('topic', '')}\n"
    header += f"Вопрос {question_num}/{total_questions}"
    msg = bot.send_message(chat_id, header)
    user_messages.append(msg.message_id)
    
    if all_text_answers:
        if question_has_images:
            for img_path in question['question_images']:
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as img:
                        msg = bot.send_photo(
                            chat_id,
                            img,
                            caption=question.get('question_text', '') if img_path == question['question_images'][0] else ''
                        )
                        user_messages.append(msg.message_id)
        else:
            if question.get('question_text'):
                msg = bot.send_message(chat_id, question.get('question_text', ''))
                user_messages.append(msg.message_id)
        
        answers_text = ""
        for ans in question['answers']:
            if ans.get('text'):
                answers_text += f"{ans['letter']}) {ans['text']}\n"
        
        if answers_text:
            msg = bot.send_message(chat_id, answers_text)
            user_messages.append(msg.message_id)
    else:
        if question_has_images:
            for img_path in question['question_images']:
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as img:
                        msg = bot.send_photo(
                            chat_id,
                            img,
                            caption=question.get('question_text', '') if img_path == question['question_images'][0] else ''
                        )
                        user_messages.append(msg.message_id)
        else:
            if question.get('question_text'):
                msg = bot.send_message(chat_id, question.get('question_text', ''))
                user_messages.append(msg.message_id)
        
        #send answers
        for ans in question['answers']:
            if len(ans.get('images', [])) > 0:
                for img_path in ans['images']:
                    if os.path.exists(img_path):
                        with open(img_path, 'rb') as img:
                            msg = bot.send_photo(
                                chat_id,
                                img,
                                caption=f"{ans['letter']})"
                            )
                            user_messages.append(msg.message_id)
            elif ans.get('text'):
                msg = bot.send_message(chat_id, f"{ans['letter']}) {ans['text']}")
                user_messages.append(msg.message_id)
    
    #send inline keyboard
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn_a = types.InlineKeyboardButton('A', callback_data='answer_A')
    btn_b = types.InlineKeyboardButton('B', callback_data='answer_B')
    btn_c = types.InlineKeyboardButton('C', callback_data='answer_C')
    btn_d = types.InlineKeyboardButton('D', callback_data='answer_D')
    btn_finish = types.InlineKeyboardButton('🛑 Завершить', callback_data='finish')
    
    markup.add(btn_a, btn_b, btn_c, btn_d)
    markup.add(btn_finish)
    
    msg = bot.send_message(chat_id, "Выберите ответ:", reply_markup=markup)
    user_messages.append(msg.message_id)
    
    return user_messages

def cleanup_messages(chat_id, session):
    if 'user_messages' in session:
        for msg_id in session['user_messages']:
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
        session['user_messages'] = []

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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_back = types.KeyboardButton('🔙 Назад')
    markup.add(btn_back)
    help_text = (
        "🤖 *Помощь по боту*\n\n"
        "Этот бот поможет вам подготовиться к ЕНТ.\n\n"
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/help - Справка\n\n"
        "/subjects - Выбор предмета для подготовки\n"
        "/probent - Пробный ЕНТ\n"
        "/stats - Статистика\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_back = types.KeyboardButton('🔙 Назад')
    markup.add(btn_back)
    bot.send_message(
        message.chat.id,
        "📊 *Ваша статистика*\n\n",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['subjects'])
def subjects_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    btn_math = types.KeyboardButton('📐 Математика')
    btn_informatics = types.KeyboardButton('💻 Информатика')
    btn_world_history = types.KeyboardButton('🌍 Всемирная история')
    btn_law = types.KeyboardButton('⚖️ Основы права')
    btn_chemistry = types.KeyboardButton('🧪 Химия')
    btn_physics = types.KeyboardButton('⚛️ Физика')
    btn_biology = types.KeyboardButton('🧬 Биология')
    btn_geography = types.KeyboardButton('🌍 География')
    btn_english = types.KeyboardButton('🇬🇧 Английский язык')
    btn_kazakh = types.KeyboardButton('🇰🇿 Казахский язык')
    btn_kazakh_lit = types.KeyboardButton('🇰🇿 Казахская литература')
    btn_russian = types.KeyboardButton('🇷🇺 Русский язык')
    btn_russian_lit = types.KeyboardButton('🇷🇺 Русская литература')
    btn_history = types.KeyboardButton('📜 История Казахстана')
    btn_math_lit = types.KeyboardButton('📊 Математическая грамотность')
    btn_read_lit = types.KeyboardButton('📖 Грамотность чтения')
    btn_back = types.KeyboardButton('🔙 Назад')
    
    markup.add(btn_math, btn_informatics, btn_world_history, btn_law,
               btn_chemistry, btn_physics, btn_biology, btn_geography,
               btn_english, btn_kazakh, btn_kazakh_lit, btn_russian,
               btn_russian_lit, btn_history, btn_math_lit, btn_read_lit, btn_back)
    
    bot.send_message(
        message.chat.id,
        "Выберите предмет для подготовки:",
        reply_markup=markup
    )

@bot.message_handler(commands=['probent'])
def prob_ent_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_mir_pravo = types.KeyboardButton('🌍 Всемирная история - ⚖️ Основы права')
    btn_fiz_mat = types.KeyboardButton('📐 Математика - ⚛️ Физика')
    btn_geo_mat = types.KeyboardButton('📐 Математика - 🌍 География')
    btn_him_fiz = types.KeyboardButton('🧪 Химия - ⚛️ Физика')
    btn_bio_him = types.KeyboardButton('🧬 Биология - 🧪 Химия')
    btn_bio_geo = types.KeyboardButton('🧬 Биология - 🌍 География')
    btn_geo_eng = types.KeyboardButton('🌍 География - 🇬🇧 Английский язык')
    btn_mir_geo = types.KeyboardButton('🌍 Всемирная история - 🌍 География')
    btn_eng_mir = types.KeyboardButton('🇬🇧 Английский язык - 🌍 Всемирная история')
    btn_kaz_kaz = types.KeyboardButton('🇰🇿 Казахский язык - 🇰🇿 Казахская литература')
    btn_rus_rus = types.KeyboardButton('🇷🇺 Русский язык - 🇷🇺 Русская литература')
    btn_mat_info = types.KeyboardButton('📐 Математика - 💻 Информатика')
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
        '📐 Математика', '💻 Информатика', '🌍 Всемирная история', '⚖️ Основы права',
        '🧪 Химия', '⚛️ Физика', '🧬 Биология', '🌍 География',
        '🇬🇧 Английский язык', '🇰🇿 Казахский язык', '🇰🇿 Казахская литература',
        '🇷🇺 Русский язык', '🇷🇺 Русская литература', '📜 История Казахстана',
        '📊 Математическая грамотность', '📖 Грамотность чтения'
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
    
    selected_questions = get_random_questions(questions, 5)
    
    user_sessions[message.chat.id] = {
        'subject': subject,
        'questions': selected_questions,
        'current_index': 0,
        'correct_answers': 0,
        'user_messages': []
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
    
    cleanup_messages(chat_id, session)
    
    question_num = session['current_index'] + 1
    total_questions = len(session['questions'])
    
    session['user_messages'] = render_question(chat_id, session, question_num, total_questions)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        bot.answer_callback_query(call.id, "Сессия не найдена")
        return
    
    if call.data == 'finish':
        cleanup_messages(chat_id, session)
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
        cleanup_messages(chat_id, session)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        
        session['current_index'] += 1
        send_question(chat_id)
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith('answer_'):
        user_answer = call.data.split('_')[1]
        current_question = session['questions'][session['current_index']]
        correct_answer = current_question['correct'].upper()
        
        result_text = f"Ваш ответ: {user_answer}"
        if user_answer == correct_answer:
            session['correct_answers'] += 1
            result_text += "\n✅ Правильно!"
        else:
            result_text += f"\n❌ Неправильно! \nПравильный ответ: {correct_answer}"
        
        markup = types.InlineKeyboardMarkup()
        btn_next = types.InlineKeyboardButton('➡️ Следующий вопрос', callback_data='next')
        btn_finish = types.InlineKeyboardButton('🛑 Завершить', callback_data='finish')
        markup.add(btn_next)
        markup.add(btn_finish)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=result_text,
            reply_markup=markup
        )
        
        bot.answer_callback_query(call.id)
        return
    
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
