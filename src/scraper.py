from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def extract_content(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in background without opening a window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get(url)
        time.sleep(5)  # Wait for the page to load completely (including JS)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Example: extract page title
        title = soup.title.string if soup.title else 'No title'
        return {
            'url': url,
            'title': title,
            'content': soup.get_text()
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    url = 'https://www.zapimoveis.com.br/aluguel/apartamentos/ce+fortaleza/?transacao=aluguel&onde=%2CCear%C3%A1%2CFortaleza%2C%2C%2C%2C%2Ccity%2CBR%3ECeara%3ENULL%3EFortaleza%2C-3.73272%2C-38.527013%2C&tipos=apartamento_residencial&precoMaximo=1000'
    result = extract_content(url)
    print(result)