import asyncio
from playwright.async_api import async_playwright

CHANNELS = {
    "Первый канал": "https://smotrettv.com/tv/public/1003-pervyj-kanal.html",
    "Россия 1": "https://smotrettv.com/tv/public/784-rossija-1.html",
    "Звезда": "https://smotrettv.com/tv/public/310-zvezda.html",
    "ТНТ": "https://smotrettv.com/tv/entertainment/329-tnt.html",
    "Россия 24": "https://smotrettv.com/tv/news/217-rossija-24.html",
    "СТС": "https://smotrettv.com/tv/entertainment/783-sts.html"

}

async def get_working_url(channel_name, page_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Можно поставить False для отладки
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        m3u8_url = None

        # Перехватываем все сетевые запросы
        async def handle_request(request):
            nonlocal m3u8_url
            url = request.url
            # Ищем ссылку на поток (обычно содержит .m3u8 и токен)
            if ".m3u8" in url and ("token=" in url or "master" in url):
                # Исключаем мелкие чанки, ищем именно плейлист
                if "tracks-" in url or "index" in url or "mono" in url:
                    m3u8_url = url

        page.on("request", handle_request)

        try:
            print(f"Заходим на страницу {channel_name}...")
            await page.goto(page_url, wait_until="networkidle", timeout=30000)
            
            # Эмулируем клик по плееру, если поток не пошел сам
            await page.click("body", timeout=5000) 
            
            # Ждем немного, чтобы плеер успел запросить поток
            for _ in range(10): 
                if m3u8_url: break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
        finally:
            await browser.close()
            
        return m3u8_url

async def main():
    for name, url in CHANNELS.items():
        real_url = await get_working_url(name, url)
        if real_url:
            print(f"--- РАБОЧАЯ ССЫЛКА ДЛЯ {name.upper()} ---")
            print(real_url)
        else:
            print(f"Не удалось найти поток для {name}")

if __name__ == "__main__":
    asyncio.run(main())
