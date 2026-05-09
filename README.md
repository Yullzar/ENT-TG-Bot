# ENT-TG-Bot

A Telegram bot to help students prepare for the Kazakhstani UNT / ЕНТ exams by serving question sets, running practice sessions and trial exams.

**Features**
- **Practice by subject:** choose a subject and get randomized questions.
- **Trial ENT:** generate full trial exams for your specialized subjects
- **Question media support:** handles question and options with images in them.

**Prerequisites**
- Python 3.8 or newer
- A Telegram bot token (see Configuration)

**Install**

Install dependencies:

```bash
pip install -r requirements.txt
```

**Configuration**

Update the `BOT_TOKEN` at the beginning of `bot.py` with your Telegram bot token:

```python
BOT_TOKEN = 'YOUR_TOKEN_HERE'
```

**Project layout**
- `bot.py` — main Telegram bot implementation and handlers
- `questions_json/` — JSON files with question banks per subject
- `media/` — images used by questions and answers

**Running**

Start the bot:

```bash
python bot.py

**Dependencies**
- See [requirements.txt](requirements.txt)

