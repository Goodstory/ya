import requests
from bs4 import BeautifulSoup
import time
import re

def get_neuro_answer(query):
    url = f'https://ya.ru/neuralsearch/?text={requests.utils.quote(query)}'
    headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      "Accept-Language": "ru,en;q=0.9",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
      "Connection": "keep-alive",
      "Referer": "https://ya.ru/",
      "Upgrade-Insecure-Requests": "1"
      
    }
    resp = requests.get(url, headers=headers, timeout=10)
    print(resp.status_code, resp.url)
    # print(resp.text)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Записать soap в файл
    with open("soap_neuro.html", "w", encoding="utf-8") as f:
        f.write(str(resp.text))
    # Находим элемент с ответом от Нейро
    neuro_section = soup.find("section", class_="FuturisGPTMessage-GroupContent")
    if not neuro_section:
        return None

    # Вытаскиваем все абзацы и списки — для полноты
    parts = []
    # Абзацы
    for p in neuro_section.find_all('div', class_='FuturisMarkdown-Paragraph'):
        parts.append(p.get_text(" ", strip=True))
    # Списки (например, цены по магазинам)
    for ul in neuro_section.find_all('ul', class_='FuturisMarkdown-UnorderedList'):
        for li in ul.find_all('li'):
            parts.append(li.get_text(" ", strip=True))
    # Остальной текст (например, если абзац не размечен)
    text = neuro_section.get_text("\n", strip=True)
    if text and text not in parts:
        parts.append(text)
    # Чистим дубли, убираем пустое
    all_text = "\n".join(sorted(set([x.strip() for x in parts if x.strip()])))
    return all_text

if __name__ == "__main__":
    queries = [
        # "цена iPhone 15",
        # "цена Samsung Galaxy S23",
        # "цена Наушники JBL",
        "цена Клин стопорный 375-2902579 УРАЛ NEXT рессора передняя"
    ]
    for q in queries:
        ans = get_neuro_answer(q)
        filename = f"neuro_answer_{re.sub('[^a-zA-Z0-9а-яА-Я]+', '_', q)[:40]}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"[{q}]\n\n")
            if ans:
                f.write(ans)
                print(f"Ответ для [{q}] сохранён в {filename}\n")
            else:
                f.write("Ответ не найден")
                print(f"Ответ для [{q}] не найден\n")
        # Пауза для аккуратности
        time.sleep(1)
