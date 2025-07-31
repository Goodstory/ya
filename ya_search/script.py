import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
import datetime

def parse_prices_from_text(text):
    # Находит все цены с пробелами/неразрывными пробелами, руб, ₽, $, €, а также фильтрует подозрительно маленькие числа (рейтинги)
    pattern = r"(?:от|до|≈)?\s*([1-9]\d{2,5}(?:[ \xa0]\d{3})*(?:[.,]\d+)?)(?:\s*(?:руб(?:\.|лей)?|₽|\$|€|eur|usd))"
    matches = re.findall(pattern, text, re.IGNORECASE)
    result = []
    for match in matches:
        value = match.replace(' ', '').replace('\xa0', '').replace(',', '.')
        try:
            val = float(value)
            if 100 <= val <= 1000000:  # Опять-таки, убираем рейтинги
                result.append(value)
        except:
            continue
    return result



def get_all_prices(query):
    # Генерируем URL запроса
    url = f'https://yandex.ru/search/?text={requests.utils.quote(query)}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        print(f"Ошибка запроса: {resp.status_code}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    texts = []
    # Парсим тексты всех сниппетов выдачи
    for snippet in soup.find_all(['div', 'span', 'li']):
        txt = snippet.get_text(separator=" ", strip=True)
        if txt:
            texts.append(txt)
    # Сливаем все тексты в одну строку и ищем все цены
    all_text = ' '.join(texts)
    prices = parse_prices_from_text(all_text)
    # Очищаем пробелы и делаем уникальные цены
    prices = [p.replace(' ', '') for p in prices]
    unique_prices = sorted(set(prices), key=prices.index)
    return unique_prices

if __name__ == "__main__":
    df = pd.read_csv("input.csv")
    all_results = []
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f'yandex_prices_{now}.txt'
    log = open(log_filename, 'w', encoding='utf-8')

    for product in df['product']:
        query = f"сколько стоит {product}"
        print(f"Парсим: {query}")
        prices = get_all_prices(query)
        all_results.append(", ".join(prices) if prices else "")
        # Логируем всё для отладки
        log.write(f"[{query}]\n")
        if prices:
            log.write("\n".join(prices) + "\n\n")
        else:
            log.write("Цен не найдено\n\n")
        log.flush()
        time.sleep(2)  # не спамим

    df['prices'] = all_results
    df.to_csv("output.csv", index=False)
    log.close()
    print(f"Готово! Цены сохранены в output.csv, подробности в {log_filename}")
