from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

llm_main = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)
