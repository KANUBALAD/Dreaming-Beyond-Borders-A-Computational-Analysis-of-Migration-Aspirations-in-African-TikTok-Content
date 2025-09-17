from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import re
import os
import random

# Hashtags to scrape
hashtags = ["ghanauknurses"]


# ---------------------- Metrics Helper ----------------------
def _parse_count(count_str):
    """Convert abbreviated counts (1.2K, 5.5M, etc.) to integers"""
    if not count_str:
        return "0"

    count_str = count_str.upper().replace(',', '')

    if 'K' in count_str:
        return str(int(float(count_str.replace('K', '')) * 1000))
    elif 'M' in count_str:
        return str(int(float(count_str.replace('M', '')) * 1000000))
    elif 'B' in count_str:
        return str(int(float(count_str.replace('B', '')) * 1000000000))
    else:
        return count_str.strip()


# ---------------------- Extract Video Metrics ----------------------
async def extract_metrics_improved(page):
    """Improved metric extraction with multiple fallbacks"""
    views, likes, shares = "0", "0", "0"

    # Method 1: Extract from HTML JSON
    try:
        page_content = await page.content()

        view_match = re.search(r'"playCount":(\d+)', page_content)
        if view_match:
            views = view_match.group(1)

        like_match = re.search(r'"diggCount":(\d+)', page_content)
        if like_match:
            likes = like_match.group(1)

        share_match = re.search(r'"shareCount":(\d+)', page_content)
        if share_match:
            shares = share_match.group(1)

        if views != "0" or likes != "0":
            return views, likes, shares
    except:
        pass

    # Method 2: Extract from visible elements
    try:
        stats_section = await page.query_selector('[data-e2e="video-views"]') or await page.query_selector(
            '[class*="video-meta-info"]'
        )

        if stats_section:
            stats_text = await stats_section.inner_text()

            views_match = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*views?', stats_text, re.IGNORECASE)
            if views_match:
                views = _parse_count(views_match.group(1))

            likes_match = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*likes?', stats_text, re.IGNORECASE)
            if likes_match:
                likes = _parse_count(likes_match.group(1))

            shares_match = re.search(r'(\d+(?:\.\d+)?[KMB]?)\s*shares?', stats_text, re.IGNORECASE)
            if shares_match:
                shares = _parse_count(shares_match.group(1))
    except:
        pass

    return views, likes, shares


# ---------------------- Extract Comments ----------------------
async def extract_comments_improved(page, video_url, all_comments):
    """Improved comment extraction"""
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        comments_turned_off = await page.query_selector('div:has-text("Comments are turned off")')
        if comments_turned_off:
            print("      ⚠️ Comments are turned off")
            return 0

        comment_elements = await page.query_selector_all('[data-e2e="comment-item"]')
        if not comment_elements:
            comment_elements = await page.query_selector_all('div[class*="comment"]')

        comment_count = 0
        for comment in comment_elements[:10]:  # Limit to 10 comments
            try:
                text_element = await comment.query_selector('[data-e2e="comment-text"]') or await comment.query_selector(
                    'p, span'
                )
                if not text_element:
                    continue

                comment_text = await text_element.inner_text()
                if not comment_text or "Log in" in comment_text:
                    continue

                author_element = await comment.query_selector('[data-e2e="comment-author-nickname"]') or await comment.query_selector(
                    'a[href*="/@"]'
                )
                author = await author_element.inner_text() if author_element else "Unknown"

                likes_element = await comment.query_selector('[data-e2e="comment-like-count"]')
                likes = await likes_element.inner_text() if likes_element else "0"

                all_comments.append({
                    "video_url": video_url,
                    "comment_author": author,
                    "comment_text": comment_text,
                    "comment_likes": likes
                })

                comment_count += 1

            except Exception as e:
                print(f"      ❌ Error extracting comment: {e}")
                continue

        return comment_count

    except Exception as e:
        print(f"      ❌ Error in comment extraction: {e}")
        return 0


# ---------------------- Main Scraper ----------------------
async def scrape_tiktok():
    async with async_playwright() as p:
        # Persistent context keeps you logged in between runs
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./tiktok_session",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-sandbox",
            ]
        )

        page = await context.new_page()
        await page.goto("https://www.tiktok.com")
        await page.wait_for_timeout(5000)

        print("⚠️ If not logged in, please log in manually in the opened browser window.")
        print("   The session will be saved, and next runs won’t need login.")

        all_videos = []
        all_comments = []

        for tag in hashtags:
            print(f"🔍 Scraping videos for #{tag}...")
            try:
                clean_tag = tag.lstrip('#')
                url = f"https://www.tiktok.com/tag/{clean_tag}" or f"https://www.tiktok.com/search?lang=en-GB&q={clean_tag}&t=1758102799453"
                print(f"Navigating to: {url}")

                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)

                # Scroll to load more
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)

                video_links = await page.query_selector_all("a[href*='/video/']")
                print(f"✅ Found {len(video_links)} video links")

                video_urls = set()
                for link in video_links:
                    href = await link.get_attribute("href")
                    if href:
                        video_urls.add(href if href.startswith("http") else f"https://www.tiktok.com{href}")

                print(f"Processing {len(video_urls)} unique videos...")

                for video_count, video_url in enumerate(list(video_urls)[:20], start=1):
                    try:
                        print(f"   📹 Processing video {video_count}: {video_url}")
                        await page.goto(video_url, timeout=30000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(3000)

                        username_match = re.search(r'/@([^/]+)/video/', video_url)
                        username = username_match.group(1) if username_match else "Unknown"

                        caption = "No caption"
                        caption_element = await page.query_selector('[data-e2e="browse-video-desc"]')
                        if caption_element:
                            caption = await caption_element.inner_text()

                        views, likes, shares = await extract_metrics_improved(page)

                        video_data = {
                            "hashtag": clean_tag,
                            "video_url": video_url,
                            "username": username,
                            "caption": caption,
                            "views": views,
                            "likes": likes,
                            "shares": shares
                        }
                        all_videos.append(video_data)

                        print(f"      ✅ Video: @{username} - {caption[:100]}...")
                        print(f"      📊 Stats - Views: {views}, Likes: {likes}, Shares: {shares}")

                        print(f"💬 Extracting comments...")
                        comments_count = await extract_comments_improved(page, video_url, all_comments)
                        print(f"      💬 Found {comments_count} comments")

                        await asyncio.sleep(random.uniform(2, 5))

                    except Exception as video_error:
                        print(f"      ❌ Error processing video: {video_error}")
                        continue

                print(f"✅ Completed #{clean_tag}")

            except Exception as e:
                print(f"⚠️ Error with hashtag #{tag}: {e}")
                continue

        # Save videos
        if all_videos:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            videos_file = f"tiktok_videos_detailed_{timestamp}.csv"
            pd.DataFrame(all_videos).to_csv(videos_file, index=False)
            print(f"✅ Saved videos to {videos_file}")

        # Save comments
        if all_comments:
            comments_file = "tiktok_comments_detailed.csv"
            pd.DataFrame(all_comments).to_csv(comments_file, index=False)
            print(f"✅ Saved comments to {comments_file}")

        print("\n📊 SUMMARY:")
        print(f"   Total videos: {len(all_videos)}")
        print(f"   Total comments: {len(all_comments)}")

        await context.close()


if __name__ == "__main__":
    asyncio.run(scrape_tiktok())
