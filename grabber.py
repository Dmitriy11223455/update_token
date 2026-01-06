import asyncio
from playwright.async_api import async_playwright

# Список каналов
CHANNELS = {
    "Первый канал": "https://smotrettv.com/tv/public/1003-pervyj-kanal.html",
    "Россия 1": "https://smotrettv.com/tv/public/784-rossija-1.html",
    "Звезда": "https://smotrettv.com/tv/public/310-zvezda.html",
    "ТНТ": "https://smotrettv.com/tv/entertainment/329-tnt.html",
    "Россия 24": "https://smotrettv.com/tv/news/217-rossija-24.html",
    "СТС": "https://smotrettv.com/tv/entertainment/783-sts.html"

}

async def get_m3u8_link(page_url):
    """Парсит страницу и ловит сетевой запрос на поток .m3u8"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        found_url = None

        # Обработчик перехвата запросов
        async def request_handler(request):
            nonlocal found_url
            url = request.url
            # Ищем ссылку, содержащую m3u8 и токен (или master/index)
            if ".m3u8" in url and "token=" in url:
                # Фильтруем, чтобы взять основной поток, а не мелкие части
                if not found_url:
                    found_url = url

        page.on("request", request_handler)

        try:
            await page.goto(page_url, wait_until="networkidle", timeout=20000)
            # Иногда нужно кликнуть по плееру, чтобы пошел поток
            await page.mouse.click(500, 300)
            await asyncio.sleep(5) # Ждем подгрузки потока
        except Exception as e:
            print(f"Ошибка на {page_url}: {e}")
        finally:
            await browser.close()
        
        return found_url

async def main():
    playlist_content = "#EXTM3U\n"
    
    print(f"--- Запуск парсинга (Январь 2026) ---")
    
    for name, page_url in CHANNELS.items():
        print(f"Обработка: {name}...")
        stream_url = await get_m3u8_link(page_url)
        
        if stream_url:
            # Добавляем в плейлист с заголовком Referer (важно для работы в плеерах)
            # Формат |Referer=... понимается многими плеерами (OTT Navigator, VLC, Televizo)
            playlist_entry = f'#EXTINF:-1,{name}\n#EXTVLCOPT:http-referrer=smotrettv.com\n{stream_url}|Referer=smotrettv.com\n'
            playlist_content += playlist_entry
            print(f" OK: Ссылка получена.")
        else:
            print(f" SKIP: Ссылку найти не удалось.")

    # Сохраняем в файл
    with open("my_playlist.m3u8", "w", encoding="utf-8") as f:
        f.write(playlist_content)
    
    print("\n--- Готово! Плейлист сохранен в файл: my_playlist.m3u8 ---")

if __name__ == "__main__":
    asyncio.run(main())
