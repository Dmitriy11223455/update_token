import asyncio
import yaml
import time
from datetime import datetime
from playwright.async_api import async_playwright

# --- КОНФИГУРАЦИЯ ---
CONFIG_FILE = "channels.yaml"
OUTPUT_FILE = "playlist.m3u8"
# --- КОНФИГУРАЦИЯ ---

async def get_stream_url(page_url):
    """
    Запускает скрытый браузер для захвата актуальной ссылки с токеном.
    """
    async with async_playwright() as p:
        # Запуск браузера в безголовом режиме (невидимый)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        found_url = None

        # Перехватываем все сетевые запросы
        async def handle_request(request):
            nonlocal found_url
            # Ищем ссылку, содержащую .m3u8 и параметр token (признак IPTV-потока)
            if ".m3u8" in request.url and "token=" in request.url:
                # Берем первую найденную ссылку основного потока
                if not found_url and "index" not in request.url: 
                    found_url = request.url

        page.on("request", handle_request)

        try:
            print(f"  > Открытие страницы: {page_url}")
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
            # Эмулируем клик для активации плеера
            await page.mouse.click(500, 300) 
            await asyncio.sleep(5) # Ждем 5 секунд на подгрузку потока
        except Exception as e:
            print(f"  [ОШИБКА] При парсинге страницы: {e}")
        finally:
            await browser.close()
        
        return found_url

def load_channels():
    """Загружает список каналов из YAML-файла."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)["channels"]
    except FileNotFoundError:
        print(f"Ошибка: Файл '{CONFIG_FILE}' не найден.")
        exit()
    except yaml.YAMLError as e:
        print(f"Ошибка чтения YAML-файла: {e}")
        exit()

async def generate_m3u_playlist():
    """Основная функция генерации плейлиста."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Запуск генерации плейлиста...")
    channels = load_channels()
    m3u_content = "#EXTM3U\n"

    for channel in channels:
        name = channel["name"]
        url = channel["url"]
        referer = channel.get("referer", "smotret.tv") # Домен по умолчанию

        stream_url = await get_stream_url(url)
        
        if stream_url:
            # Добавляем в плейлист: #EXTINF, URL, и Referer для совместимости с плеерами (VLC, OTT)
            m3u_content += f'#EXTINF:-1 group-title="TV",{name}\n'
            m3u_content += f'#EXTVLCOPT:http-referrer={referer}\n'
            # Используем формат URL|Referer= для универсальности
            m3u_content += f'{stream_url}|Referer={referer}\n'
            print(f"  [OK] Ссылка для '{name}' получена.")
        else:
            print(f"  [ПРОПУСК] Не удалось получить ссылку для '{name}'.")

    # Сохраняем результат
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Плейлист '{OUTPUT_FILE}' успешно обновлен.")

if __name__ == "__main__":
    # Запускаем один раз для создания файла
    asyncio.run(generate_m3u_playlist())
    print("\nСкрипт завершил работу. Если вам нужно автообновление, используйте 'updater.py' или 'server.py'.")
