
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

def web_search(query, num_results=10, cx=None):
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_WEB_SEARCH_KEY")
    if not cx:
        raise ValueError("É necessário fornecer o parâmetro 'cx' (ID do mecanismo de busca personalizado do Google)")
    if not api_key:
        raise ValueError("Chave de API do Google não encontrada no .env (GOOGLE_API_WEB_SEARCH_KEY)")
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": num_results
    }
    response = requests.get(search_url, params=params)
    data = response.json()
    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        })
    return results

# Exemplo de uso:
if __name__ == "__main__":
    print("Executando")
    query = "apartamentos em fortaleza"
    cx = "f250cd15b14884f9f"  # Substitua pelo seu ID do mecanismo de busca personalizado
    search_results = web_search(query, cx=cx)
    print("Result: ", search_results)
    for result in search_results:
        print(result)