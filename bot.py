import os
import tempfile
import json
import logging
import shelve
from dotenv import load_dotenv
import requests
from telegram import Update, InlineKeyboardButton, WebAppInfo, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_community.agent_toolkits import GoogleCalendarToolkit
from langchain.agents import AgentType, initialize_agent


# --- LangChain Models ---
# Custom ChatGrok class (as langchain_xai is not available)
class ChatGrok:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def __call__(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gemma-7b-it", # or other grok model
            "messages": messages,
            "temperature": 0.7,
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# Initialize models
models = {
    "gpt": ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY),
    "claude": ChatAnthropic(model="claude-3-5-sonnet-20240620", api_key=ANTHROPIC_API_KEY),
    "grok": ChatGrok(api_key=GROK_API_KEY),
}

# --- User Data Persistence (using shelve) ---
def get_user_data():
    return shelve.open("user_data.db", writeback=True)

def close_user_data(user_data):
    user_data.close()

def get_user_memory(user_id):
    with get_user_data() as user_data:
        if user_id not in user_data:
            user_data[user_id] = {
                "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                "model": "gpt"
            }
        return user_data[user_id]["memory"]

def get_user_model(user_id):
    with get_user_data() as user_data:
        if user_id not in user_data:
            user_data[user_id] = {
                "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                "model": "gpt"
            }
        return user_data[user_id]["model"]

def set_user_model(user_id, model_name):
    with get_user_data() as user_data:
        if user_id not in user_data:
            user_data[user_id] = {
                "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                "model": "gpt"
            }
        if model_name in models:
            user_data[user_id]["model"] = model_name
            return True
        return False

# --- Telegram Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am your task management assistant. "
        "I can help you manage your projects, sprints, and tasks. "
        "Use /model [gpt/claude/grok] to switch AI models. "
        "Send me a text or voice message to get started.",
    )

async def miniapp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a button to open the Mini App."""
    keyboard = [
        [InlineKeyboardButton("Open Mini App", web_app=WebAppInfo(url="https://telegram.me/DurgerKingBot/menu"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click the button to open the Mini App:", reply_markup=reply_markup)

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles data received from the Mini App."""
    data = json.loads(update.effective_message.web_app_data.data)
    user_id = update.effective_user.id

    # Example of updating user context from Mini App data
    # This is a placeholder, you should adapt it to your Mini App's data structure
    if 'tasks' in data:
        # Update user's tasks in memory
        memory = get_user_memory(user_id)
        memory.chat_memory.add_user_message(f"Mini App update: {data}")
        await update.message.reply_text("Your context has been updated from the Mini App.")
    else:
        await update.message.reply_text(f"Received data from Mini App: {data}")


async def model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switches the AI model."""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /model [gpt/claude/grok]")
        return
    model_name = context.args[0].lower()
    if set_user_model(user_id, model_name):
        await update.message.reply_text(f"Switched to {model_name} model.")
    else:
        await update.message.reply_text(f"Invalid model: {model_name}. Please choose from gpt, claude, or grok.")

# --- Message Handlers ---
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles voice messages by transcribing them and then processing the text."""
    voice_file = await context.bot.get_file(update.message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio_file:
        await voice_file.download_to_drive(temp_audio_file.name)
        temp_audio_path = temp_audio_file.name

    try:
        url = "https://api.elevenlabs.io/v1/speech-to-text/v1/speech-to-text/convert"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
        }
        files = {
            "file": (os.path.basename(temp_audio_path), open(temp_audio_path, 'rb'), 'audio/ogg')
        }
        data = {
            "model_id": "eleven_multilingual_v2",
            "language_code": "en",
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        transcription = response.json()["text"]

        # Now, process the transcription as a text message
        update.message.text = transcription
        await handle_message(update, context)

    except Exception as e:
        logger.error(f"Error transcribing voice message: {e}")
        await update.message.reply_text("Sorry, I couldn't transcribe your voice message. Please try again.")
    finally:
        os.remove(temp_audio_path)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages and sends them to the LLM agent."""
    user_id = update.effective_user.id
    text = update.message.text

    memory = get_user_memory(user_id)
    model_name = get_user_model(user_id)
    llm = models[model_name]

    # Initialize Google Calendar Toolkit
    toolkit = GoogleCalendarToolkit()
    tools = toolkit.get_tools()

    # Create an agent with the Google Calendar tools
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )

    try:
        response = await agent.arun(input=text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("model", model))
    application.add_handler(CommandHandler("miniapp", miniapp))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()
