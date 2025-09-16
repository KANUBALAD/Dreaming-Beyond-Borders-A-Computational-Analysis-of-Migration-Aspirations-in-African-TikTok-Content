from tiktokapipy.api import TikTokAPI
import asyncio
import pandas as pd

# Hashtags to scrape
hashtags = ["GhanaInUK"]

async def main():
    api = TikTokAPI()
    all_data = []

    for tag in hashtags:
        print(f"🔍 Scraping videos for #{tag}...")
        try:
            hashtag = await api.hashtag(name=tag)
            videos = []
            async for video in hashtag.videos(count=30):
                videos.append(video)
            
            for video in videos:
                video_data = {
                    "video_url": f"https://www.tiktok.com/@{video.author.username}/video/{video.id}",
                    "username": video.author.username,
                    "caption": video.desc,
                    "views": video.stats.play_count,
                    "likes": video.stats.digg_count,
                    "shares": video.stats.share_count,
                    "date": video.create_time
                }
                print(video_data)  # Debugging log
                all_data.append(video_data)

        except Exception as e:
            print(f"⚠️ Error fetching videos for #{tag}: {e}")
            continue

    # Save the data to a CSV file
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv("tiktok_data.csv", index=False)
        print("✅ Data saved to tiktok_data.csv")
    else:
        print("❌ No data collected")

if __name__ == "__main__":
    asyncio.run(main())