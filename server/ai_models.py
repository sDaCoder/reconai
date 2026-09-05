import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_groq_model(model_name = "openai/gpt-oss-120b", temperature=0):
    return ChatGroq(model=model_name, temperature=temperature)