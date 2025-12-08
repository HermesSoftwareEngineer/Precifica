from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv

load_dotenv()

llm_main = ChatVertexAI(
    model_name="gemini-2.5-flash",
)