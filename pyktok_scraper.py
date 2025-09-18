from tiktokapipy.api import TikTokAPI
import asyncio
import pandas as pd

# Hashtags to scrape
hashtags = ["GhanaInUK"]

async def main():
    async with TikTokAPI() as api:
        all_data = []

        for tag in hashtags:
            print(f"🔍 Scraping videos for #{tag}...")
            try:
                hashtag = await api.hashtag(name=tag)
                videos = await hashtag.videos(count=30)  # Adjust count as needed
                
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
        df = pd.DataFrame(all_data)
        df.to_csv("tiktok_data.csv", index=False)
        print("✅ Data saved to tiktok_data.csv")

if __name__ == "__main__":
    asyncio.run(main())