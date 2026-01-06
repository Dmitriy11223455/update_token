import random
import os
from playwright.async_api import async_playwright

# КОНФИГУРАЦИЯ
CHANNELS = {
    "Первый канал": "smotrettv.com",
    "Россия 1": "smotrettv.com"
}

# Шаблон ссылки для DRM-play (добавлены параметры для стабильности)
STREAM_BASE_URL = "https://server.smotrettv.com/{channel_id}.m3u8?token={token}"

async def get_tokens_and_make_playlist():
    async with async_playwright() as p:
        # Для работы на ПК лучше ставить headless=False, чтобы видеть процесс
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()

        login = os.getenv('LOGIN', 'ВАШ_ЛОГИН')
        password = os.getenv('PASSWORD', 'ВАШ_ПАРОЛЬ')

        try:
            await page.goto("smotrettv.com")
            await page.fill('input[name="email"]', login)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Ошибка авторизации: {e}")

        # Начало формирования заголовка для DRM-play
        playlist_data = "#EXTM3U\n"
        
        for name, url in CHANNELS.items():
            print(f"Обработка: {name}...")
            current_token = None

            def handle_request(request):
                nonlocal current_token
                if "token=" in request.url:
                    try:
                        current_token = request.url.split("token=")[1].split("&")[0]
                    except:
                        pass

            page.on("request", handle_request)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(8) 

                if current_token:
                    channel_id = url.split("/")[-1]
                    stream_url = STREAM_BASE_URL.format(channel_id=channel_id, token=current_token)
                    
                    # ФОРМАТ ДЛЯ DRM-PLAY
                    playlist_data += f'#EXTINF:-1, {name}\n'
                    # Добавляем свойства для корректного подхвата плеером DRM-play
                    playlist_data += f'#KODIPROP:inputstream.adaptive.license_type=widevine\n'
                    playlist_data += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
                    playlist_data += f'{stream_url}\n'
                    print(f"Токен получен.")
                else:
                    print(f"Токен не найден для {name}.")

            except Exception as e:
                print(f"Ошибка на {name}: {e}")

        # Сохраняем результат
        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write(playlist_data)
        
        print("\nПлейлист для DRM-play готов.")
        await browser.close()

if name == "main":
    asyncio.run(get_tokens_and_make_playlist())
ter.py' или 'server.py'.")
