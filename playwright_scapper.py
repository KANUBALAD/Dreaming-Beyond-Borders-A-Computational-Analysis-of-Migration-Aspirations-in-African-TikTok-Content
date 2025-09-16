from playwright.async_api import async_playwright
import pandas as pd
import asyncio

hashtags = ["GhanaInUK"]

async def scrape_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        all_data = []

        for tag in hashtags:
            print(f"🔍 Scraping videos for #{tag}...")
            try:
                await page.goto(f"https://www.tiktok.com/tag/{tag}", timeout=60000)
                # Extract video data (adjust selectors as needed)
                videos = await page.query_selector_all("div[data-e2e='video-item']")
                if not videos:
                    print(f"No videos found for #{tag}")
                    continue

                for video in videos[:10]:
                    video_url = await video.get_attribute("href")
                    username = await video.query_selector("span[data-e2e='author-uniqueId']").inner_text()
                    caption = await video.query_selector("p[data-e2e='video-desc']").inner_text()
                    views = await video.query_selector("strong[data-e2e='video-views']").inner_text()
                    video_data = {
                        "video_url": video_url,
                        "username": username,
                        "caption": caption,
                        "views": views,
                    }
                    print(f"Video URL: {video_url}, Username: {username}, Caption: {caption}, Views: {views}")
                    all_data.append(video_data)
            except Exception as e:
                print(f"⚠️ Error fetching videos for #{tag}: {e}")
                continue

        # Save to CSV
        df = pd.DataFrame(all_data)
        df.to_csv("playwright_tiktok_data.csv", index=False)
        print("✅ Data saved to playwright_tiktok_data.csv")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_tiktok())
    
    
    
   