def parse_items_v2(text, query):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    items = []
    last_src = ''
    last_date = ''
    for i, line in enumerate(lines):
        # Проверяем источник
        src_match = re.search(r'([\w-]+\.(?:ru|com|рф|su|net|org|ua|kz))', line, re.I)
        if src_match:
            last_src = src_match.group(1)
        
        # Ищем цену
        price_regex = r'(?:цена|от|по|=|–|-|—|≈|~)?\s*([\d\s.,]{2,})\s*(₽|р|руб(?![а-я])|руб\.|\$|usd|eur|€)'
        for match in re.finditer(price_regex, line, re.I):
            val = match.group(1).replace(' ', '').replace(',', '.')
            curr = match.group(2)
            price = f"{val}{curr}"
            
            # Дата — ищем в строке или выше/ниже
            ctx = " ".join([lines[i-1] if i > 0 else '', line, lines[i+1] if i < len(lines)-1 else ''])
            date_match = re.search(r'(\d{1,2}\s+[а-яА-ЯёЁ]+\s+\d{4})', ctx)
            date = date_match.group(1) if date_match else last_date
            
            # Источник — из текущей или запомненной строки
            src = src_match.group(1) if src_match else last_src

            # Фильтр: цена длиной не меньше 2, есть домен
            if len(val) > 1 and src:
                items.append({'query': query, 'price': price, 'date': date, 'src': src, 'line': line})
        
        # Дата
        date_match = re.search(r'(\d{1,2}\s+[а-яА-ЯёЁ]+\s+\d{4})', line)
        if date_match:
            last_date = date_match.group(1)
    return items