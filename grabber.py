import asyncio
import os
import re
from playwright.async_api import async_playwright

# КОНФИГУРАЦИЯ (Ваши ссылки добавлены)
CHANNELS = {
    "Первый канал": "https://smotrettv.com/tv/public/1003-pervyj-kanal.html",
    "Россия 1": "https://smotrettv.com/tv/public/784-rossija-1.html",
    "Звезда": "https://smotrettv.com/tv/public/310-zvezda.html",
    "ТНТ": "https://smotrettv.com/tv/entertainment/329-tnt.html",
    "Россия 24": "https://smotrettv.com/tv/news/217-rossija-24.html",
    "СТС": "https://smotrettv.com/tv/entertainment/783-sts.html"
}

# Шаблон: цифры перед названием в ссылке станут ID потока
STREAM_BASE_URL = "https://server.smotrettv.com{channel_id}.m3u8?token={token}"

async def get_tokens_and_make_playlist():
    async with async_playwright() as p:
        # headless=True обязателен для GitHub Actions 2026
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        login = os.getenv('LOGIN')
        password = os.getenv('PASSWORD')

        # 1. Авторизация
        try:
            print("Авторизация на сайте...")
            await page.goto("smotrettv.com")
            await page.fill('input[name="email"]', login)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Ошибка входа: {e}")

        playlist_data = "#EXTM3U\n"
        
        # 2. Обход каналов
        for name, url in CHANNELS.items():
            print(f"Обработка: {name}...")
            current_token = None

            def handle_request(request):
                nonlocal current_token
                # Ищем токен в сетевых запросах плеера
                if "token=" in request.url:
                    try:
                        # Извлекаем значение между 'token=' и '&'
                        current_token = request.url.split("token=")[1].split("&")[0]
                    except:
                        pass

            page.on("request", handle_request)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(10) # Ждем прогрузки видео и появления токена

                if current_token:
                    # Извлекаем ID из ссылки (например, из '1003-pervyj-kanal.html' берем '1003')
                    raw_id = url.split("/")[-1].split("-")[0]
                    
                    stream_url = STREAM_BASE_URL.format(channel_id=raw_id, token=current_token)
                    
                    # Формат для Lampa / DRM-play
                    playlist_data += f'#EXTINF:-1, {name}\n'
                    playlist_data += f'#KODIPROP:inputstream.adaptive.license_type=widevine\n'
                    playlist_data += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
                    playlist_data += f'{stream_url}\n'
                    print(f"Успех: {name} (ID: {raw_id})")
                else:
                    print(f"Токен для {name} не найден. Проверьте подписку на аккаунте.")

            except Exception as e:
                print(f"Ошибка при загрузке {name}: {e}")

        # 3. Сохранение (название файла как в вашей инструкции)
        filename = "playlist_8f2d9k1l.m3u"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(playlist_data)
        
        print(f"\nГотово! Файл {filename} создан.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_tokens_and_make_playlist())
