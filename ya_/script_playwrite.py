import asyncio
from playwright.async_api import async_playwright
import time
import datetime
import re
import csv
import os

QUERIES = [
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

def parse_items(text, query):
    # Регулярки для цены, источника, даты
    items = []
    # Разбиваем на строки (в ответах часто по строкам)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for i, line in enumerate(lines):
        # контекст — эта строка + предыдущая/следующая
        ctx = " ".join([
            lines[i-1] if i > 0 else '',
            line,
            lines[i+1] if i < len(lines)-1 else ''
        ])
        # Ищем дату
        date_match = re.search(r'(\d{1,2}\s+[а-яА-ЯёЁ]+\s+\d{4})', line)
        date = date_match.group(1) if date_match else ""

        # Ищем цену
        # price_match = re.search(r'(\d[\d\s.,]+)\s*(₽|р|руб(?![а-я])|руб\.|\$|usd|eur|€)', line, re.I)
        # price = price_match.group(0).replace(' ', '').replace(',', '.') if price_match else ""
        
        # ищем ключевые слова рядом с ценой
        price_regex = r'(?:цена|по|за|от|стоимость|стоит|=|–|-|—|≈|~)?\s*([\d\s.,]{2,})\s*(₽|р|руб(?![а-я])|руб\.|\$|usd|eur|€)'
        results = []
        for match in re.finditer(price_regex, ctx, re.I):
            # print(match)
            raw = match.group(0)
            val = match.group(1).replace(' ', '').replace(',', '.')
            curr = match.group(2)
            # print(f"Найдена цена: {val} {curr} в контексте: {ctx}")
            # Отфильтровать "цена — 4,5Р" (но не "4,5Р за штуку")
            # Можно также фильтровать по длине (цена вряд ли меньше 2 знаков)
            if len(val) < 2:
                continue
            # фильтруем очевидные веса и оценки (например, "4,5Р" если встречается слово "оценка" или "класс")
            # bad_words = ['класс', 'отзыв', 'оценка', 'вес', 'длина', 'штук', 'шт.', 'шт', 'мм', 'кг', 'л', 'литр', 'длина', 'г', 'ml']
            # if any(bw in ctx.lower() for bw in bad_words):
            #     continue
            # чтобы не было дубликатов
            result_str = f"{val}{curr}"
            print(f"Найдена цена: {result_str} в контексте: {ctx}")
            if result_str not in results:
                results.append(result_str)
        print(f"Найденные цены в строке: {results}")
        price = ', '.join(results) if results else None
        print(f"Цена: {price}")

        # Ищем источник (домен)
        src_match = re.search(r'([\w-]+\.(?:ru|com|рф|su|net|org|ua|kz))', line, re.I)
        src = src_match.group(1) if src_match else ""

        # Сохраняем если есть цена + источник
        if price and src:
            items.append({
                'query': query,
                'price': price,
                'date': date,
                'src': src,
                'line': line
            })
    return items

async def get_neuro_answer(playwright, query):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        locale='ru-RU',
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    await page.goto("https://ya.ru/neuralsearch/")
    await page.wait_for_selector('textarea.FuturisTextarea-Input', timeout=30000)
    await page.fill('textarea.FuturisTextarea-Input', query)
    
    now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs('screenshots', exist_ok=True)
    await page.screenshot(path=f"screenshots/screenshot_result{now}_fill.png")
    
    await page.click('.FuturisMiniButton_type_submit')
    await asyncio.sleep(8)  
    await page.wait_for_selector('.FuturisGPTMessage-GroupContent', timeout=50000)
    await asyncio.sleep(8)  # ждём допечатывания (можно менять)
    await page.screenshot(path=f"screenshots/screenshot_result{now}_answer.png")
    
    try:
        answer = await page.inner_text('.FuturisGPTMessage-GroupContent .FuturisGPTMessage-GroupContentComponentWrapper .FuturisMarkdown')
    except Exception:
        answer = ""
    await browser.close()
    return answer.strip()

async def main():
    all_results = []
    csv_rows = []
    async with async_playwright() as playwright:
        for q in QUERIES:
            print(f"Запрос: {q}")
            try:
                answer = await get_neuro_answer(playwright, q)
                print("Ответ нейро:\n", answer)
                items = parse_items(answer, q)
            except Exception as e:
                print(f"Ошибка для '{q}':", e)
                answer = ""
                items = []
            all_results.append({'query': q, 'answer': answer, 'items': items})
            # Для csv — если нет цен, то пустая строка
            if items:
                for item in items:
                    csv_rows.append([item['query'], item['price'], item['date'], item['src'], item['line']])
            else:
                csv_rows.append([q, "Цен не найдено", "", "", ""])
            time.sleep(2)

    # Сохраняем все ответы и сырые строки в TXT
    with open(f'neuro_results{datetime.datetime.now().strftime("%Y-%m-%d")}.txt', 'w', encoding='utf-8') as f:
        for res in all_results:
            f.write(f"[{res['query']}]\n")
            f.write(res['answer'] + '\n')
            if res['items']:
                for it in res['items']:
                    f.write(f"Цена: {it['price']}, Дата: {it['date']}, Источник: {it['src']}\n")
            else:
                f.write("Цен не найдено\n")
            f.write('\n')

    # Сохраняем в csv
    with open(f'neuro_prices_{datetime.datetime.now().strftime("%Y-%m-%d")}.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Запрос', 'Цена', 'Дата', 'Источник', 'Строка'])
        writer.writerows(csv_rows)

    print("Сохранено в neuro_results.txt и neuro_prices.csv")

if __name__ == '__main__':
    asyncio.run(main())
