from tiktokapipy.api import TikTokAPI
import asyncio
import pandas as pd

# Hashtags to scrape
hashtags = ["GhanaInUK"]

async def main():
    all_data = []
    all_comments = []

    try:
        api = TikTokAPI()
        
        # Let's first check what methods are available
        print("Available API methods:")
        print([method for method in dir(api) if not method.startswith('_')])

        for tag in hashtags:
            print(f"🔍 Scraping videos for #{tag}...")
            try:
                # Use the challenge method for hashtag search
                challenge_obj = await api.challenge(tag)
                print(f"Challenge object: {type(challenge_obj)}")
                print(f"Challenge attributes: {[attr for attr in dir(challenge_obj) if not attr.startswith('_')]}")
                
                # Try to get videos from the challenge
                if hasattr(challenge_obj, 'videos'):
                    videos = challenge_obj.videos
                    print(f"Found videos attribute, type: {type(videos)}")
                    
                    # If videos is async iterable
                    if hasattr(videos, '__aiter__'):
                        video_count = 0
                        async for video in videos:
                            if video_count >= 30:  # Limit to 30 videos
                                break
                            
                            # Get video ID for linking comments
                            video_id = getattr(video, 'id', f'unknown_{len(all_data)}')
                            video_url = getattr(video, 'url', f"https://www.tiktok.com/@{getattr(video.author, 'username', 'unknown')}/video/{video_id}")
                            
                            # Get comments for each video
                            print(f"   Fetching comments for video {video_id}...")
                            try:
                                if hasattr(video, 'comments'):
                                    comment_count = 0
                                    async for comment in video.comments:
                                        if comment_count >= 50:  # Limit to 50 comments per video
                                            break
                                        
                                        comment_data = {
                                            "video_id": video_id,
                                            "video_url": video_url,
                                            "video_username": getattr(video.author, 'username', 'unknown') if hasattr(video, 'author') else 'unknown',
                                            "hashtag": tag,
                                            "comment_text": getattr(comment, 'text', ''),
                                            "comment_author": getattr(comment.author, 'username', 'unknown') if hasattr(comment, 'author') else 'unknown',
                                            "comment_likes": getattr(comment, 'digg_count', 0),
                                            "comment_date": getattr(comment, 'create_time', ''),
                                            "comment_replies": getattr(comment, 'reply_count', 0)
                                        }
                                        all_comments.append(comment_data)
                                        comment_count += 1
                            except Exception as e:
                                print(f"   Could not fetch comments for video {video_id}: {e}")
                            
                            # Video data
                            video_data = {
                                "video_id": video_id,
                                "video_url": video_url,
                                "username": getattr(video.author, 'username', 'unknown') if hasattr(video, 'author') else 'unknown',
                                "author_follower_count": getattr(video.author, 'follower_count', 0) if hasattr(video, 'author') else 0,
                                "hashtag": tag,
                                "caption": getattr(video, 'desc', ''),
                                "views": getattr(video.stats, 'play_count', 0) if hasattr(video, 'stats') else 0,
                                "likes": getattr(video.stats, 'digg_count', 0) if hasattr(video, 'stats') else 0,
                                "shares": getattr(video.stats, 'share_count', 0) if hasattr(video, 'stats') else 0,
                                "comments_count": getattr(video.stats, 'comment_count', 0) if hasattr(video, 'stats') else 0,
                                "date": getattr(video, 'create_time', ''),
                                "duration": getattr(video, 'duration', 0),
                                "music_title": getattr(video.music, 'title', '') if hasattr(video, 'music') else '',
                                "music_author": getattr(video.music, 'author', '') if hasattr(video, 'music') else ''
                            }
                            print(f"   ✅ Video data collected: {video_data['username']} - {video_data['caption'][:50]}...")
                            all_data.append(video_data)
                            video_count += 1
                            
                            # Add a small delay to avoid rate limiting
                            await asyncio.sleep(1)
                            
                    # If videos is a regular list
                    elif hasattr(videos, '__iter__'):
                        for i, video in enumerate(videos):
                            if i >= 30:  # Limit to 30 videos
                                break
                            # Same video processing logic would go here
                            
                else:
                    print(f"Challenge object doesn't have videos attribute")
                    print(f"Available attributes: {[attr for attr in dir(challenge_obj) if not attr.startswith('_')]}")

            except Exception as e:
                print(f"⚠️ Error fetching videos for #{tag}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error initializing API: {e}")
        return

    # Save the data to CSV files
    if all_data:
        # Save video data
        df_videos = pd.DataFrame(all_data)
        df_videos.to_csv("tiktok_videos.csv", index=False)
        print(f"✅ Video data saved to tiktok_videos.csv ({len(all_data)} videos)")
        
        # Save comments data separately
        if all_comments:
            df_comments = pd.DataFrame(all_comments)
            df_comments.to_csv("tiktok_comments.csv", index=False)
            print(f"✅ Comments saved to tiktok_comments.csv ({len(all_comments)} comments)")
        else:
            print("⚠️ No comments collected")
            
        # Save summary statistics
        summary = {
            "total_videos": len(all_data),
            "total_comments": len(all_comments),
            "hashtags_scraped": hashtags,
            "avg_comments_per_video": len(all_comments) / len(all_data) if all_data else 0,
            "total_views": sum([video.get('views', 0) for video in all_data]),
            "total_likes": sum([video.get('likes', 0) for video in all_data])
        }
        
        summary_df = pd.DataFrame([summary])
        summary_df.to_csv("scraping_summary.csv", index=False)
        print(f"✅ Summary saved to scraping_summary.csv")
        
        # Print summary
        print("\n📊 SCRAPING SUMMARY:")
        print(f"   Videos collected: {summary['total_videos']}")
        print(f"   Comments collected: {summary['total_comments']}")
        print(f"   Average comments per video: {summary['avg_comments_per_video']:.2f}")
        print(f"   Total views: {summary['total_views']:,}")
        print(f"   Total likes: {summary['total_likes']:,}")
        
    else:
        print("❌ No data collected")

if __name__ == "__main__":
    asyncio.run(main())