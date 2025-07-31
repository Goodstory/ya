import asyncio
from playwright.async_api import async_playwright
import time
import datetime
import re

QUERIES = [
    # "сколько стоит iPhone 15",
    # "сколько стоит Samsung Galaxy S23",
    # "сколько стоит Наушники JBL",
    'список цен с источником, датой и ценой на "Клин стопорный 375-2902579 УРАЛ NEXT рессора передняя"',
    'список цен с источником, датой и ценой на "Элемент фильтрующий топливный PL 420 110-16-004 КамАЗ Евро в сборе"',
    'список цен с источником, датой и ценой на "Гвоздь 4*100"',
    'список цен с источником, датой и ценой на "Очиститель Технониколь Professional TN528382 0,5л"',
    'список цен с источником, датой и ценой на "(эталон код НМК 000000006995) Ремень 14*10-987 вентиляторный"',
    'список цен с источником, датой и ценой на "Бензин АИ-92 (л)"',
    'список цен с источником, датой и ценой на "Рукавицы Спецобъединение РУК 018 всесезонные сукно шинельное"',
    'список цен с источником, датой и ценой на "Стартер редукторный StartVOLT LSt 0306 3M3-406, 409 ГАЗ, УАЗ 12В"',
    'список цен с источником, датой и ценой на "Бензогенератор сварочный SWATT PG5500WE 5кВт"',
    'список цен с источником, датой и ценой на "Набор инструментов Кратон TS-30 multi 131 2 28 09 030 131пред."',
    'список цен с источником, датой и ценой на "Лист горячекатанный B1500mm L6000mm s5mm Ст3 ГОСТ 19903-2015 353,25кг"',
    'список цен с источником, датой и ценой на "Лист B1500mm L6000mm s8mm Ст3 ГОСТ 19903-2015 565,2кг"',
    'список цен с источником, датой и ценой на "Уголок 75756mm Ст3пс горячекатанный ГОСТ 8509-93"',
    'список цен с источником, датой и ценой на "Аптечка Астра Люкс автомобильная"',
    'список цен с источником, датой и ценой на "Кислород технический"',
    'список цен с источником, датой и ценой на "Кастрюля 3,5л сталь нержавеющая"',
    'список цен с источником, датой и ценой на "Электрод Inforce MP-3 D3мм"',
    'список цен с источником, датой и ценой на "Сверло D22mm сталь Р6М5 конический хвостовик по металлу"',
    'список цен с источником, датой и ценой на "Сверло D30mm сталь Р6М5 конический хвостовик по металлу"',
    'список цен с источником, датой и ценой на "Перчатки рабочие летние"',
    'список цен с источником, датой и ценой на "Сверло D16.5mm сталь Р6М5 цилиндрический хвостовик по металлу"',
    'список цен с источником, датой и ценой на "Наклейка опасный груз 3/2002 (дизельное топливо В400 * L300mm"',
    'список цен с источником, датой и ценой на "Наклейка Знак опасности АК 315 / В250*"',
    'список цен с источником, датой и ценой на "Труба ГОСТ D108mm s3,5mm прямошовная электросварная ГОСТ 10704-91"',
    'список цен с источником, датой и ценой на "Кисть КМ 80"',
    'список цен с источником, датой и ценой на "Известь гашеная Movatex T02369 5кг"',
    'список цен с источником, датой и ценой на "Строп канатный УСК1 4т L5m 1-вет."',
    'список цен с источником, датой и ценой на "Лист горячекатанный B1250mm L2500mm s3mm Ст3 ГОСТ 19903-2015 73,59кг"',
    'список цен с источником, датой и ценой на "Резьба DN50мм"',
]

async def get_neuro_answer(playwright, query):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        locale='ru-RU',
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    await page.goto("https://ya.ru/neuralsearch/")
    # Найди поле поиска и введи запрос
    await page.wait_for_selector('textarea.FuturisTextarea-Input', timeout=30000)
    await page.fill('textarea.FuturisTextarea-Input', query)
    
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    await page.screenshot(path=f"screenshots/screenshot_result{now}_fill.png")
    
    await page.click('.FuturisMiniButton_type_submit')
    
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    await page.screenshot(path=f"screenshots/screenshot_result{now}_submit.png")
    
    # Ждём появления ответа
    await page.wait_for_selector('.FuturisGPTMessage-GroupContent', timeout=50000)
    # Получаем весь текст ответа (может быть несколько блоков)
    await asyncio.sleep(10)  # чуть подождать для "допечатывания" (можно увеличить)
    
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    await page.screenshot(path=f"screenshots/screenshot_result{now}_answer.png")
    
    answer = await page.inner_text('.FuturisGPTMessage-GroupContent .FuturisGPTMessage-GroupContentComponentWrapper .FuturisMarkdown')
    with open('page_content.html', 'w', encoding='utf-8') as f:
      f.write(answer)
    await browser.close()
    return answer.strip()

def extract_prices(text):
    # Универсальная регулярка для всех валют и цен
    prices = re.findall(r'[\d\s.,]+(?:₽|р|руб(?![а-я])|руб\.|\$|usd|eur|€)', text, re.I)
    # Очистка пробелов
    prices = [p.replace(' ', '').replace(',', '.') for p in prices]
    return prices or ["Цен не найдено"]

async def main():
    all_results = []
    async with async_playwright() as playwright:
        for q in QUERIES:
            print(f"Запрос: {q}")
            try:
                answer = await get_neuro_answer(playwright, q)
                print("Ответ нейро:\n", answer)
                prices = extract_prices(answer)
            except Exception as e:
                print(f"Ошибка для '{q}':", e)
                answer = ""
                prices = ["Цен не найдено"]
            all_results.append({'query': q, 'answer': answer, 'prices': prices})
            time.sleep(2)

    # Сохраняем в файл
    with open('neuro_results.txt', 'w', encoding='utf-8') as f:
        for res in all_results:
            f.write(f"[{res['query']}]\n")
            f.write(f"{res['answer']}\n")
            f.write("Цены: " + ", ".join(res['prices']) + "\n\n")

    print("Сохранено в neuro_results.txt")

if __name__ == '__main__':
    asyncio.run(main())
