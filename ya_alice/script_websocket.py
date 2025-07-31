import websocket
import json
import pandas as pd
import time
import uuid
import re
import threading
import datetime

AUTH_TOKEN = "effd5a3f-fd42-4a18-83a1-61766a6d0924"
UUID = "00000000000007837294221573829591"
ICOOKIE = "2AV6xrewrUNFLbhHyVKXp0RbeKopVmM+XUUesHn98g9JfqBW6LeADLl7XcPd2/nVTPAKi6J4Ipd8gMpLbeCtHT5dYaI="

def make_message_id():
    return str(uuid.uuid4())

class AliceScraper:
    def __init__(self, auth_token, uuid, icookie):
        self.auth_token = auth_token
        self.uuid = uuid
        self.icookie = icookie
        self.session_id = None
        self.ws = None
        self.all_prices = set()
        self.message_id = None
        self.last_dialog_id = None
        self.last_msg_time = time.time()
        self.lock = threading.Lock()
        now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.responses_log_filename = f'alice_responses_{now}.txt'
        self.responses_log = open(self.responses_log_filename, 'w', encoding='utf-8')

    def extract_prices_from_text(self, text):
        prices = set()
        # регэксп: ищет 34999, 34 999, 34,999, 34.999 и валюту
        for match in re.finditer(r'(\d[\d\s.,]*)\s*([₽рруб$€]|usd|eur)', text, re.IGNORECASE):
            value = match.group(1).replace(' ', '').replace(',', '.')
            currency = match.group(2).replace('р', '₽').replace('руб', '₽').replace('usd', '$').replace('eur', '€')
            prices.add(f"{value}{currency}")
        return prices

    def on_message(self, ws, message):
        with self.lock:
            self.last_msg_time = time.time()
        try:
            data = json.loads(message)
            self.responses_log.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n\n")
            self.responses_log.flush()
        except Exception as e:
            print(f"Ошибка при парсинге сообщения: {e}")
            return

        # 1. Сохраняем session_id
        if 'directive' in data and data['directive']['header']['name'] == 'SynchronizeStateResponse':
            self.session_id = data['directive']['payload']['SessionId']

        # 2. Смотрим DeferredAliceResponse и все варианты json_response
        if 'directive' in data and 'payload' in data['directive']:
            payload = data['directive']['payload']

            # Новый стиль: payload['json_response']['base_response']['cards'][...]['text_card']['text']
            if 'json_response' in payload and 'base_response' in payload['json_response']:
                cards = payload['json_response']['base_response'].get('cards', [])
                for card in cards:
                    # Варианты, где лежит текст
                    if 'text_card' in card and 'text' in card['text_card']:
                        text = card['text_card']['text']
                        self.all_prices |= self.extract_prices_from_text(text)
                    elif 'text' in card:
                        self.all_prices |= self.extract_prices_from_text(card['text'])

            # Старый стиль: payload['response']['cards'][...]['text']
            elif 'response' in payload:
                cards = payload['response'].get('cards', [])
                for card in cards:
                    text = card.get('text') or card.get('title') or card.get('subtitle') or card.get('description')
                    if text:
                        self.all_prices |= self.extract_prices_from_text(text)

    def close_log(self):
        self.responses_log.close()

    def on_error(self, ws, error):
        print("!!! Ошибка:", error)

    def on_close(self, ws, code, msg):
        print(f">>> Сокет закрыт: {code} {msg}")

    def on_open(self, ws):
        sync_message = {
            "event": {
                "header": {
                    "namespace": "System",
                    "name": "SynchronizeState",
                    "seqNumber": 1,
                    "messageId": make_message_id()
                },
                "payload": {
                    "auth_token": self.auth_token,
                    "uuid": self.uuid,
                    "vins": {
                        "application": {
                            "app_id": "ru.yandex.webstandalone.desktop",
                            "platform": "mac"
                        }
                    },
                    "supported_features": [
                        "supports_bso_answer", "open_link"
                    ],
                    "request": {
                        "experiments": []
                    },
                    "speechkitVersion": "4.16.7",
                    "icookie": self.icookie
                }
            }
        }
        ws.send(json.dumps(sync_message))
        time.sleep(1)

        text = self.product_query
        msg_id = make_message_id()
        self.message_id = msg_id
        dialog_id = make_message_id()
        self.last_dialog_id = dialog_id

        text_message = {
            "event": {
                "header": {
                    "namespace": "Vins",
                    "name": "TextInput",
                    "messageId": msg_id,
                    "seqNumber": 2
                },
                "payload": {
                    "application": {
                        "app_id": "ru.yandex.webstandalone.desktop",
                        "app_version": "standalone-2025-07-21-0-1",
                        "platform": "mac",
                        "os_version": "mozilla/5.0 (macintosh; intel mac os x 10_15_7) applewebkit/537.36 (khtml, like gecko) chrome/138.0.0.0 safari/537.36",
                        "uuid": self.uuid,
                        "lang": "ru-RU",
                        "client_time": time.strftime('%Y%m%dT%H%M%S'),
                        "timezone": "Asia/Chita",
                        "timestamp": str(int(time.time()))
                    },
                    "header": {
                        "request_id": msg_id,
                        "dialog_id": dialog_id,
                        "dialog_type": 2
                    },
                    "request": {
                        "event": {
                            "type": "text_input",
                            "text": text,
                            "attached_files": []
                        },
                        "voice_session": False,
                        "experiments": [],
                        "additional_options": {
                            "bass_options": {
                                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                                "screen_scale_factor": 2
                            },
                            "origin_domain": "yandex.ru",
                            "supported_features": [],
                            "unsupported_features": [],
                            "icookie": self.icookie
                        },
                        "environment_state": {
                            "endpoints": [
                                {
                                    "id": self.uuid,
                                    "capabilities": []
                                }
                            ]
                        }
                    },
                    "format": "audio/ogg;codecs=opus",
                    "mime": "audio/webm;codecs=opus",
                    "topic": "desktopgeneral",
                    "alice_2_settings": {
                        "preset": "",
                        "mode": "Pro"
                    }
                }
            }
        }
        ws.send(json.dumps(text_message))

    def get_prices(self, product_name, silent_seconds=2, max_total_seconds=25):
        self.all_prices = set()
        self.product_query = f"сколько стоит {product_name}"
        self.last_msg_time = time.time()

        self.ws = websocket.WebSocketApp(
            "wss://uniproxy.alice.yandex.ru/uni.ws",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=[
                "Origin: https://alice.yandex.ru",
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            ]
        )

        def ws_run():
            self.ws.run_forever()

        thread = threading.Thread(target=ws_run)
        thread.start()

        start = time.time()
        while thread.is_alive():
            with self.lock:
                since_last_msg = time.time() - self.last_msg_time
            if since_last_msg > silent_seconds:
                self.ws.close()
                break
            if time.time() - start > max_total_seconds:
                self.ws.close()
                break
            time.sleep(0.2)
        thread.join()
        return ', '.join(self.all_prices) if self.all_prices else None

if __name__ == "__main__":
    df = pd.read_csv("input.csv")
    scraper = AliceScraper(AUTH_TOKEN, UUID, ICOOKIE)
    prices = []

    for product in df['product']:
        price = scraper.get_prices(product)
        prices.append(price)
        time.sleep(2)

    df['prices'] = prices
    df.to_csv("output.csv", index=False)
    scraper.close_log()
    print(f"Результат сохранён в output.csv\nЛоги сохранены в {scraper.responses_log_filename}")
