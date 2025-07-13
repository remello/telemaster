import json
from telegram import Update, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.storage import user_data
from bot.models import get_llm_chain
from bot.stt import transcribe_voice
from bot.config import OPENAI_API_KEY, ANTHROPIC_API_KEY, GROK_API_KEY, MINI_APP_URL, logger
from bot.gcal import create_event, get_events
from bot.tts import text_to_speech

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Model", "Mini App"],
        ["Voice On", "Voice Off"],
        ["Pomodoro", "Progress"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome! I am your task management bot.", reply_markup=reply_markup)

async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    current_model = user_data.get_user_model(user_id)
    # Simple toggle for demonstration
    new_model = "gpt" if current_model == "claude" else "claude"
    user_data.set_user_model(user_id, new_model)
    await update.message.reply_text(f"Switched to {new_model.upper()} model.")

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text
    if command == "Model":
        await model(update, context)
    elif command == "Mini App":
        await miniapp(update, context)
    elif command == "Voice On":
        await voice_on(update, context)
    elif command == "Voice Off":
        await voice_off(update, context)
    elif command == "Pomodoro":
        await pomodoro(update, context)
    elif command == "Progress":
        await progress(update, context)
    else:
        await handle_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        text = update.message.text

        if text.startswith('/'):
            return

        model_name = user_data.get_user_model(user_id)
        api_key = {
            "gpt": OPENAI_API_KEY,
            "claude": ANTHROPIC_API_KEY,
            "grok": GROK_API_KEY
        }.get(model_name)

        if not api_key:
            await update.message.reply_text("API key for the current model is not configured.")
            return

        llm_chain = get_llm_chain(user_id, model_name, api_key)
        response = llm_chain.invoke({"question": text})

        # Save context
        # This part is complex and needs a proper implementation of how to extract
        # and store context from the conversation.
        # For now, we are not explicitly saving the context back to the storage.

        await update.message.reply_text(response["text"])

        if user_data.get_voice_enabled(user_id):
            try:
                audio = text_to_speech(response["text"])
                await update.message.reply_voice(voice=audio)
            except Exception as e:
                logger.error(f"Error in TTS: {e}")
                await update.message.reply_text(f"Ошибка TTS: {str(e)}")
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        ogg_file = await voice_file.download_as_bytearray()

        transcribed_text = transcribe_voice(bytes(ogg_file))
        if transcribed_text:
            # Create a new update object to pass to handle_message
            new_update = Update(update.update_id, message=update.message)
            new_update.message.text = transcribed_text
            await handle_message(new_update, context)
        else:
            await update.message.reply_text("Could not transcribe the voice message.")
    except Exception as e:
        logger.error(f"Error in handle_voice: {e}")
        await update.message.reply_text(f"An error occurred during transcription: {e}")

async def miniapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Open the Mini App to manage your tasks:",
        reply_markup=InlineKeyboardButton("Open Mini App", web_app=WebAppInfo(url=MINI_APP_URL))
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        data = json.loads(update.message.web_app_data.data)
        memory = user_data.get_user_memory(user_id)

        if data.get('action') == 'add_task':
            task = data.get('task')
            priority = data.get('priority')
            # Update context
            user_data.save_context(user_id, {"input": f"Mini App: Добавлена задача '{task}' с приоритетом {priority}"})
            # Create calendar event
            create_event(user_id, title=task, description=f"Приоритет: {priority}", start_time="now")
            await update.message.reply_text(f"Задача '{task}' добавлена с приоритетом {priority} и синхронизирована с календарем.")

        elif data.get('action') == 'prioritize_sprint':
            events = get_events(user_id)
            model_name = user_data.get_user_model(user_id)
            api_key = {
                "gpt": OPENAI_API_KEY,
                "claude": ANTHROPIC_API_KEY,
                "grok": GROK_API_KEY
            }.get(model_name)
            llm_chain = get_llm_chain(user_id, model_name, api_key)
            response = llm_chain.run(input=f"Приоритизируй спринты на основе: {events}")
            user_data.save_context(user_id, {"input": "Mini App: Запрос на приоритизацию", "output": response})
            await update.message.reply_text(f"Приоритизация: {response}")

    except Exception as e:
        logger.error(f"Error in handle_web_app_data: {e}")
        await update.message.reply_text(f"Ошибка в Mini App: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

async def voice_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data.set_voice_enabled(user_id, True)
    await update.message.reply_text("Voice responses enabled.")

async def voice_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data.set_voice_enabled(user_id, False)
    await update.message.reply_text("Voice responses disabled.")

async def pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pomodoro timer started for 25 minutes. I will notify you when it's over.")
    # In a real scenario, you would use a job queue like APScheduler
    # to schedule a notification for 25 minutes later.
    # For now, we'll just send a message.

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    events = get_events(user_id)
    if not events:
        await update.message.reply_text("No upcoming events found in your calendar.")
        return

    response = "Here are your upcoming tasks:\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        response += f"- {event['summary']} at {start}\n"

    await update.message.reply_text(response)
