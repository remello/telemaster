import json
from telegram import Update, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from bot.storage import user_data
from bot.models import get_llm_chain
from bot.stt import transcribe_voice
from bot.config import OPENAI_API_KEY, ANTHROPIC_API_KEY, GROK_API_KEY, MINI_APP_URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! I am your task management bot.")

async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.args:
        model_name = context.args[0].lower()
        if model_name in ["gpt", "claude", "grok"]:
            user_data.set_user_model(user_id, model_name)
            await update.message.reply_text(f"Switched to {model_name.upper()} model.")
        else:
            await update.message.reply_text("Invalid model. Use /model [gpt/claude/grok]")
    else:
        current_model = user_data.get_user_model(user_id)
        await update.message.reply_text(f"Current model is {current_model.upper()}. Use /model [gpt/claude/grok] to switch.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

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

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    ogg_file = await voice_file.download_as_bytearray()

    try:
        transcribed_text = transcribe_voice(bytes(ogg_file))
        if transcribed_text:
            # Create a new update object to pass to handle_message
            new_update = Update(update.update_id, message=update.message)
            new_update.message.text = transcribed_text
            await handle_message(new_update, context)
        else:
            await update.message.reply_text("Could not transcribe the voice message.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred during transcription: {e}")

async def miniapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Open the Mini App to manage your tasks:",
        reply_markup=InlineKeyboardButton("Open Mini App", web_app=WebAppInfo(url=MINI_APP_URL))
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = json.loads(update.message.web_app_data.data)

    # Update user context from Mini App data
    user_data.set_user_context(user_id, data)

    await update.message.reply_text("Your context has been updated from the Mini App.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Log the error
    print(f"Update {update} caused error {context.error}")
