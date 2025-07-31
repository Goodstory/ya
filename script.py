import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Входной и выходной файлы
INPUT_CSV = 'input.csv'    # столбец с товарами: "product"
OUTPUT_CSV = 'output.csv'

# Функция поиска цены на alice.yandex.ru
def get_price(product):
    query = f'цена {product}'
    url = f'https://alice.yandex.ru/search?text={requests.utils.quote(query)}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  # Имитация браузера
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Пример парсинга цены (в реальности может быть иначе! Проверьте структуру страницы)
        price = None
        # Попробуем найти первую цену (можно доработать)
        for span in soup.find_all('span'):
            text = span.get_text()
            if text and any(c.isdigit() for c in text) and '₽' in text:
                price = text.strip()
                break
        return price
    except Exception as e:
        print(f"Ошибка для товара '{product}': {e}")
        return None

# Чтение товаров из файла
df = pd.read_csv(INPUT_CSV)

# Добавим столбец с ценами
prices = []
for i, row in df.iterrows():
    product = row['product']
    price = get_price(product)
    prices.append(price)
    print(f"{product}: {price}")
    time.sleep(2)  # задержка между запросами, чтобы не забанили

df['price'] = prices

# Сохраняем результат
df.to_csv(OUTPUT_CSV, index=False)
print(f"Результат сохранён в {OUTPUT_CSV}")
