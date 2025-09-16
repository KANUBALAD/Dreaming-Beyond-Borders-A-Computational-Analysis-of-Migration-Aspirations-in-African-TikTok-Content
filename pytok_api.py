from tiktokapipy.api import TikTokAPI
import asyncio
import pandas as pd

# Hashtags to scrape
hashtags = ["GhanaInUK"]

async def main():
    api = TikTokAPI()
    all_data = []

    # Let's first check what methods are available
    print("Available API methods:")
    print([method for method in dir(api) if not method.startswith('_')])

    for tag in hashtags:
        print(f"🔍 Scraping videos for #{tag}...")
        try:
            # Try different possible method names
            if hasattr(api, 'hashtag_videos'):
                videos = await api.hashtag_videos(tag, count=30)
            elif hasattr(api, 'get_hashtag'):
                hashtag_obj = await api.get_hashtag(tag)
                videos = hashtag_obj.videos
            elif hasattr(api, 'search'):
                videos = await api.search(f"#{tag}", count=30)
            else:
                print("No suitable method found for hashtag search")
                continue
            
            for video in videos:
                video_data = {
                    "video_url": getattr(video, 'url', f"https://www.tiktok.com/@{getattr(video.author, 'username', 'unknown')}/video/{getattr(video, 'id', 'unknown')}"),
                    "username": getattr(video.author, 'username', 'unknown') if hasattr(video, 'author') else 'unknown',
                    "caption": getattr(video, 'desc', ''),
                    "views": getattr(video.stats, 'play_count', 0) if hasattr(video, 'stats') else 0,
                    "likes": getattr(video.stats, 'digg_count', 0) if hasattr(video, 'stats') else 0,
                    "shares": getattr(video.stats, 'share_count', 0) if hasattr(video, 'stats') else 0,
                    "date": getattr(video, 'create_time', '')
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