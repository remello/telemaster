from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# from langchain_xai import ChatGrok # Assuming this exists or is custom
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from bot.storage import user_data

# A custom ChatGrok implementation might be needed if langchain_xai is not available
# For now, we'll use a placeholder
class ChatGrok:
    def __init__(self, api_key):
        pass
    def invoke(self, messages):
        # This is a placeholder. A real implementation would make an API call to Grok.
        return {"content": "Grok is not yet implemented."}


def get_model(model_name, api_key):
    if model_name == "gpt":
        return ChatOpenAI(api_key=api_key, model_name="gpt-4o")
    elif model_name == "claude":
        return ChatAnthropic(api_key=api_key, model_name="claude-3-5-sonnet")
    elif model_name == "grok":
        return ChatGrok(api_key=api_key)
    else:
        raise ValueError("Unknown model")

def get_llm_chain(user_id, model_name, api_key):
    llm = get_model(model_name, api_key)

    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are a helpful assistant and a project management mentor."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
    )

    memory_json = user_data.get_user_context(user_id)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    if memory_json:
        # This part needs careful implementation based on how context is stored
        pass

    llm_chain = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)
    return llm_chain
