import asyncio
import yaml
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Настройки
CONFIG_FILE = "channels.yaml"
OUTPUT_FILE = "playlist.m3u8"
UPDATE_INTERVAL = 6 * 3600  # 6 часов в секундах

async def get_stream_url(page_url):
    """Запускает браузер и ловит актуальную ссылку с токеном"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        found_url = None

        # Перехват сетевых запросов
        async def handle_request(request):
            nonlocal found_url
            if ".m3u8" in request.url and "token=" in request.url:
                if not found_url: # Берем первую подходящую ссылку
                    found_url = request.url

        page.on("request", handle_request)

        try:
            await page.goto(page_url, wait_until="networkidle", timeout=20000)
            await page.mouse.click(500, 300) # Клик по плееру для активации
            await asyncio.sleep(5) # Ожидание подгрузки потока
        except Exception as e:
            print(f"  Ошибка при парсинге {page_url}: {e}")
        finally:
            await browser.close()
        
        return found_url

def load_channels():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["channels"]

async def update_playlist():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Начало обновления плейлиста...")
    channels = load_channels()
    m3u_content = "#EXTM3U\n"

    for channel in channels:
        name = channel["name"]
        url = channel["url"]
        print(f" Обработка: {name}...")
        
        stream_url = await get_stream_url(url)
        
        if stream_url:
            # Добавляем ссылку с заголовком Referer для обхода блокировок
            m3u_content += f'#EXTINF:-1,{name}\n'
            m3u_content += f'#EXTVLCOPT:http-referrer=smotrettv.com\n'
            m3u_content += f'{stream_url}|Referer=smotrettv.com\n'
            print(f"  [OK] Ссылка получена")
        else:
            print(f"  [FAIL] Не удалось получить ссылку")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Плейлист обновлен! Следующее обновление через 6 часов.")

async def main():
    while True:
        await update_playlist()
        await asyncio.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Скрипт остановлен пользователем.")
