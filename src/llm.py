from langchain_google_vertexai import ChatVertexAI
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

llm = ChatVertexAI(
    model_name="gemini-2.5-flash",
)