import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_groq_model(model_name = "openai/gpt-oss-120b", temperature=0):
    return ChatGroq(model=model_name, temperature=temperature)

def get_openai_model(model_name = "gpt-4o-mini", temperature=0):
    return ChatOpenAI(model=model_name, temperature=temperature)