import telebot
from telebot import types
import json
import random
import os

BOT_TOKEN = '8289594090:AAF5_oPZuw7MAYsQ5lWBnPoBGaQqRZGrV0o'
#BOT_TOKEN = 'YOUR_TOKEN_HERE'
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

PROFILE_PAIRS = {
    '🌍 Всемирная история - ⚖️ Основы права': ('🌍 Всемирная история', '⚖️ Основы права'),
    '📐 Математика - ⚛️ Физика': ('📐 Математика', '⚛️ Физика'),
    '📐 Математика - 🌍 География': ('📐 Математика', '🌍 География'),
    '🧪 Химия - ⚛️ Физика': ('🧪 Химия', '⚛️ Физика'),
    '🧬 Биология - 🧪 Химия': ('🧬 Биология', '🧪 Химия'),
    '🧬 Биология - 🌍 География': ('🧬 Биология', '🌍 География'),
    '🌍 География - 🇬🇧 Английский язык': ('🌍 География', '🇬🇧 Английский язык'),
    '🌍 Всемирная история - 🌍 География': ('🌍 Всемирная история', '🌍 География'),
    '🇬🇧 Английский язык - 🌍 Всемирная история': ('🇬🇧 Английский язык', '🌍 Всемирная история'),
    '🇰🇿 Казахский язык - 🇰🇿 Казахская литература': ('🇰🇿 Казахский язык', '🇰🇿 Казахская литература'),
    '🇷🇺 Русский язык - 🇷🇺 Русская литература': ('🇷🇺 Русский язык', '🇷🇺 Русская литература'),
    '📐 Математика - 💻 Информатика': ('📐 Математика', '💻 Информатика'),
}

BASE_SUBJECTS = {
    '📜 История Казахстана': 20,
    '📖 Грамотность чтения': 10,
    '📊 Математическая грамотность': 10,
}

user_sessions = {}

def load_questions(subject_file):
    """Load and parse questions from a JSON file by subject."""
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
    """Return a random sample of questions (or all if fewer than count)."""
    if len(questions) <= count:
        return questions
    return random.sample(questions, count)

def send_chunked_message(chat_id, text):
    """Send long text in chunks (max 4000 chars per message)."""
    message_ids = []
    if not text:
        return message_ids

    max_length = 4000
    for start in range(0, len(text), max_length):
        msg = bot.send_message(chat_id, text[start:start + max_length])
        message_ids.append(msg.message_id)
    return message_ids

def send_question_image(chat_id, img_path, caption, user_messages, first_image=False):
    """Send an image with optional caption, handling long captions via chunking."""
    with open(img_path, 'rb') as img:
        safe_caption = caption if first_image and len(caption or '') <= 1000 else ''
        msg = bot.send_photo(chat_id, img, caption=safe_caption)
        user_messages.append(msg.message_id)

    if first_image and caption and len(caption) > 1000:
        user_messages.extend(send_chunked_message(chat_id, caption))

    return user_messages

def sync_trial_subject(session):
    """Sync and return the current subject for trial ENT session."""
    if not session.get('profile_subjects') or not session.get('questions'):
        return None

    if session['current_index'] >= len(session['questions']):
        return None

    current_subject = session['question_subjects'][session['current_index']]
    session['current_subject'] = current_subject

    if current_subject in session.get('subjects_order', []):
        session['current_subject_idx'] = session['subjects_order'].index(current_subject)

    return current_subject

def generate_trial_ent_questions(subject1, subject2):
    """Generate trial exam questions: base subjects + 30 questions per profile subject."""
    questions_by_subject = {}
    
    for subject, count in BASE_SUBJECTS.items():
        subject_file = SUBJECT_FILES.get(subject)
        if subject_file:
            questions = load_questions(subject_file)
            selected = get_random_questions(questions, count)
            questions_by_subject[subject] = selected
    
    for subject in [subject1, subject2]:
        subject_file = SUBJECT_FILES.get(subject)
        if subject_file:
            questions = load_questions(subject_file)
            selected = get_random_questions(questions, 30)
            questions_by_subject[subject] = selected
    
    return questions_by_subject

def render_question(chat_id, session, question_num, total_questions, skip_header=False):
    """Render and send question with images and answer buttons."""
    question = session['questions'][session['current_index']]
    user_messages = []
    
    question_has_images = len(question.get('question_images', [])) > 0
    
    for ans in question['answers']:
        if len(ans.get('images', [])) > 0:
            all_text_answers = False
            break
    else:
        all_text_answers = True
    
    # Header is only needed for regular (non‑trial) sessions. In trial ENT we build a combined
    # header in `send_question` to avoid duplicate messages.
    # In regular practice sessions we show a header with the subject and overall question count.
    # For the trial ENT flow (`profile_subjects` present) the header is constructed separately
    # in `send_question`, so we suppress it here. The `skip_header` flag is kept for backward
    # compatibility, but we also guard against accidental calls during a trial session.
    if not skip_header and not session.get('profile_subjects'):
        header = f"{session['current_subject']} | {question.get('topic', '')}\n"
        header += f"Вопрос {question_num}/{total_questions}"
        msg = bot.send_message(chat_id, header)
        user_messages.append(msg.message_id)
    
    if all_text_answers:
        if question_has_images:
            for img_path in question['question_images']:
                if os.path.exists(img_path):
                    user_messages = send_question_image(
                        chat_id,
                        img_path,
                        question.get('question_text', ''),
                        user_messages,
                        first_image=(img_path == question['question_images'][0])
                    )
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
                    user_messages = send_question_image(
                        chat_id,
                        img_path,
                        question.get('question_text', ''),
                        user_messages,
                        first_image=(img_path == question['question_images'][0])
                    )
        else:
            if question.get('question_text'):
                msg = bot.send_message(chat_id, question.get('question_text', ''))
                user_messages.append(msg.message_id)
        
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

def render_subject_navigation(chat_id, session):
    """Build navigation keyboard for moving between trial exam subjects."""
    subjects = session['subjects_order']
    current_idx = session['current_subject_idx']
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if current_idx > 0:
        btn_prev = types.KeyboardButton('⬅️ Предыдущий предмет')
        markup.add(btn_prev)
    
    if current_idx < len(subjects) - 1:
        btn_next = types.KeyboardButton('➡️ Следующий предмет')
        markup.add(btn_next)
    
    btn_finish = types.KeyboardButton('🛑 Завершить экзамен')
    btn_back = types.KeyboardButton('🔙 Назад')
    markup.add(btn_finish, btn_back)
    
    return markup

def cleanup_messages(chat_id, session):
    """Delete all user messages from current session."""
    if 'user_messages' in session:
        for msg_id in session['user_messages']:
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
        session['user_messages'] = []

def show_trial_ent_stats(chat_id, session):
    """Display trial exam statistics by subject."""
    stats = {}
    
    for subject, answers in session.get('subject_answers', {}).items():
        correct = sum(1 for a in answers if a.get('correct', False))
        total = len(answers)
        stats[subject] = {'correct': correct, 'total': total}
    
    stats_text = "📊 *Статистика пробного ЕНТ*\n\n"
    total_correct = 0
    total_questions = 0
    
    for subject, data in stats.items():
        percentage = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        stats_text += f"*{subject}*\n"
        stats_text += f"Правильно: {data['correct']} из {data['total']} ({percentage:.1f}%)\n\n"
        total_correct += data['correct']
        total_questions += data['total']
    
    total_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
    stats_text += f"*Общий итог*\n"
    stats_text += f"Правильно: {total_correct} из {total_questions} ({total_percentage:.1f}%)"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_back = types.KeyboardButton('🔙 Назад')
    markup.add(btn_back)
    
    bot.send_message(chat_id, stats_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command; show main menu."""
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
    """Handle /help command; show available commands."""
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
    """Handle /stats command; show user statistics."""
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
    """Handle /subjects command; show all available subjects."""
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
    """Handle /probent command; show profile subject pairs for trial exams."""
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
    """Route text messages to appropriate handler based on content."""
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
    elif message.text in PROFILE_PAIRS:
        subject1, subject2 = PROFILE_PAIRS[message.text]
        start_trial_ent(message, subject1, subject2)
    elif message.text in [
        '📐 Математика', '💻 Информатика', '🌍 Всемирная история', '⚖️ Основы права',
        '🧪 Химия', '⚛️ Физика', '🧬 Биология', '🌍 География',
        '🇬🇧 Английский язык', '🇰🇿 Казахский язык', '🇰🇿 Казахская литература',
        '🇷🇺 Русский язык', '🇷🇺 Русская литература', '📜 История Казахстана',
        '📊 Математическая грамотность', '📖 Грамотность чтения'
    ]:
        subject_selected(message)
    elif message.text == '⬅️ Предыдущий предмет':
        navigate_subject(message, -1)
    elif message.text == '➡️ Следующий предмет':
        navigate_subject(message, 1)
    elif message.text == '🛑 Завершить экзамен':
        finish_trial_ent(message)
    else:
        bot.send_message(
            message.chat.id,
            "Используйте меню для навигации или введите /start для возврата в главное меню."
        )

def start_trial_ent(message, subject1, subject2):
    """Start a trial ENT session with two profile subjects."""
    questions_by_subject = generate_trial_ent_questions(subject1, subject2)
    
    if not questions_by_subject:
        bot.send_message(message.chat.id, "Ошибка при загрузке вопросов. Попробуйте позже.")
        return
    
    subjects_order = list(BASE_SUBJECTS.keys()) + [subject1, subject2]
    
    all_questions = []
    question_subjects = []
    for subject in subjects_order:
        if subject in questions_by_subject:
            for q in questions_by_subject[subject]:
                all_questions.append(q)
                question_subjects.append(subject)
    
    user_sessions[message.chat.id] = {
        'subject': 'Пробный ЕНТ',
        'questions': all_questions,
        'question_subjects': question_subjects,
        'subjects_order': subjects_order,
        'current_subject_idx': 0,
        'current_index': 0,
        'correct_answers': 0,
        'user_messages': [],
        'profile_subjects': (subject1, subject2),
        'subject_answers': {s: [] for s in subjects_order},
        'answered_indices': set()
    }
    
    send_question(message.chat.id)

def navigate_subject(message, direction):
    """Navigate to previous or next subject in trial exam (direction: -1 or 1)."""
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session or not session.get('profile_subjects'):
        return
    
    current_subject = sync_trial_subject(session)
    if current_subject is None:
        return

    current_subject_idx = session.get('current_subject_idx', 0)
    new_subject_idx = current_subject_idx + direction

    while 0 <= new_subject_idx < len(session['subjects_order']):
        new_subject = session['subjects_order'][new_subject_idx]
        subject_indices = [
            i for i, s in enumerate(session['question_subjects'])
            if s == new_subject
        ]
        if not subject_indices:
            new_subject_idx += direction
            continue

        answered_indices = session.get('answered_indices', set())
        subject_completed = all(i in answered_indices for i in subject_indices)
        if subject_completed:
            new_subject_idx += direction
            continue

        session['current_subject_idx'] = new_subject_idx
        session['current_index'] = next(
            (i for i in subject_indices if i not in answered_indices),
            subject_indices[0]
        )
        send_question(chat_id)
        return

    bot.send_message(
        chat_id,
        "Нет доступных предметов в этом направлении."
    )

def finish_trial_ent(message):
    """End trial exam and show final statistics."""
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        return
    
    show_trial_ent_stats(chat_id, session)
    del user_sessions[chat_id]

def subject_selected(message):
    """Start a practice session for the selected subject."""
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
        'current_subject': subject,
        'questions': selected_questions,
        'current_index': 0,
        'correct_answers': 0,
        'user_messages': []
    }
    
    send_question(message.chat.id)

def send_question(chat_id):
    """Render and send the next question from current session."""
    session = user_sessions.get(chat_id)
    if not session:
        return
    
    if session.get('profile_subjects'):
        if session['current_index'] >= len(session['questions']):
            show_trial_ent_stats(chat_id, session)
            del user_sessions[chat_id]
            return
        
        current_subject = sync_trial_subject(session)
        if current_subject is None:
            return
        
        # All questions up to the current index belong to the current subject.
        subject_questions = [i for i, s in enumerate(session['question_subjects']) 
                           if s == current_subject and i <= session['current_index']]
        # The displayed question number should reflect the position within the subject, regardless of whether it has been answered.
        question_in_subject = len(subject_questions)
        total_in_subject = len([i for i, s in enumerate(session['question_subjects']) 
                               if s == current_subject])
        
        # Build a single header that includes current subject progress and overall answered count.
        nav_markup = render_subject_navigation(chat_id, session)
        answered = len(session.get('answered_indices', set()))
        total_questions = len(session['questions'])
        header_text = (
            f"📚 Текущий предмет: {current_subject}\n"
            f"Вопрос {question_in_subject} из {total_in_subject}\n"
            f"Отвечено: {answered}/{total_questions}"
        )
        msg = bot.send_message(chat_id, header_text, reply_markup=nav_markup)

        session['user_messages'].append(msg.message_id)

        question_num = session['current_index'] + 1
        # Pass skip_header=True to avoid duplicate subject header inside render_question.
        session['user_messages'].extend(
            render_question(chat_id, session, question_num, total_questions, skip_header=True)
        )
    else:
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
        
        question_num = session['current_index'] + 1
        total_questions = len(session['questions'])
        
        session['user_messages'] = render_question(chat_id, session, question_num, total_questions)

@bot.callback_query_handler()
def callback_handler(call):
    """Handle button callbacks: answer selection, next question, finish exam."""
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        bot.answer_callback_query(call.id, "Сессия не найдена")
        return
    
    if call.data == 'finish':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn_back = types.KeyboardButton('🔙 Назад')
        markup.add(btn_back)
        
        if session.get('profile_subjects'):
            show_trial_ent_stats(chat_id, session)
        else:
            bot.send_message(
                chat_id,
                f"🛑 Тест завершен досрочно!\n\nПравильных ответов: {session['correct_answers']} из {len(session['questions'])}",
                reply_markup=markup
            )
        del user_sessions[chat_id]
        bot.answer_callback_query(call.id)
        return
    
    if call.data == 'next':
        # Remove buttons from the result message instead of deleting it
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        except:
            pass
        
        session['current_index'] += 1
        send_question(chat_id)
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith('answer_'):
        user_answer = call.data.split('_')[1]
        if session.get('profile_subjects') and session['current_index'] in session.get('answered_indices', set()):
            bot.answer_callback_query(call.id, "Этот вопрос уже был отвечен")
            return

        current_question = session['questions'][session['current_index']]
        correct_answer = current_question['correct'].upper()
        
        result_text = f"Ваш ответ: {user_answer}"
        is_correct = user_answer == correct_answer
        
        if is_correct:
            session['correct_answers'] += 1
            result_text += "\n✅ Правильно!"
        else:
            result_text += f"\n❌ Неправильно! \nПравильный ответ: {correct_answer}"
        
        if 'subject_answers' in session:
            current_subject = session.get('current_subject', 'Неизвестно')
            if current_subject in session['subject_answers']:
                session['subject_answers'][current_subject].append({
                    'correct': is_correct
                })
        
        if 'answered_indices' in session:
            session['answered_indices'].add(session['current_index'])

        # Update the header message (first message in user_messages) only for trial ENT sessions.
        # Regular subject sessions do not have a dedicated header message, so we skip editing to avoid breaking the flow.
        if session.get('profile_subjects') and session.get('user_messages'):
            header_msg_id = session['user_messages'][0]
            answered = len(session.get('answered_indices', set()))
            total_questions = len(session['questions'])
            current_subject = session.get('current_subject', '')
            # Determine the position of the current question within its subject (1‑based).
            question_in_subject = len([
                i for i, s in enumerate(session['question_subjects'])
                if s == current_subject and i <= session['current_index']
            ])
            total_in_subject = len([
                i for i, s in enumerate(session['question_subjects'])
                if s == current_subject
            ])
            header_text = (
                f"📚 Текущий предмет: {current_subject}\n"
                f"Вопрос {question_in_subject} из {total_in_subject}\n"
                f"Отвечено: {answered}/{total_questions}"
            )
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=header_msg_id,
                    text=header_text,
                    reply_markup=render_subject_navigation(chat_id, session)
                )
            except Exception:
                pass

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
