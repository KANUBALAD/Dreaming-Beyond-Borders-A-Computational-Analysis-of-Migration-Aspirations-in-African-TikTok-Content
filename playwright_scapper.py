
from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import re
import os

# hashtags = ["ghanauknurses", "GhanaInUK", "GhanaInUSA"]
hashtags = ["ghanauknurses"]
# hashtags = ["GhanaToUKNursing"]

async def scrape_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        all_videos = []
        all_comments = []

        for tag in hashtags:
            print(f"🔍 Scraping videos for #{tag}...")
            try:
                clean_tag = tag.lstrip('#')
                url = f"https://www.tiktok.com/tag/{clean_tag}"
                print(f"Navigating to: {url}")
                
                await page.goto(url, timeout=60000, wait_until="networkidle")
                await page.wait_for_timeout(5000)
                
                # Scroll to load more videos
                print("📜 Loading more videos by scrolling...")
                for scroll_count in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)
                
                # Get video links
                video_links = await page.query_selector_all("a[href*='/video/']")
                print(f"✅ Found {len(video_links)} video links")
                
                if not video_links:
                    print("❌ No video links found")
                    continue

                # Extract unique video URLs
                video_urls = set()
                for link in video_links[:150]:  # Limit to first 30
                    href = await link.get_attribute("href")
                    if href and href not in video_urls:
                        if href.startswith("http"):
                            video_urls.add(href)
                        else:
                            video_urls.add(f"https://www.tiktok.com{href}")
                
                print(f"Processing {len(video_urls)} unique videos...")
                
                video_count = 0
                for video_url in list(video_urls)[:100]:  # Process max 10 videos per hashtag for testing
                    try:
                        print(f"   📹 Processing video {video_count + 1}: {video_url}")
                        
                        # Navigate to individual video page
                        await page.goto(video_url, timeout=30000, wait_until="networkidle")
                        await page.wait_for_timeout(3000)
                        
                        # Extract username from URL
                        username_match = re.search(r'/@([^/]+)/video/', video_url)
                        username = username_match.group(1) if username_match else "Unknown"
                        
                        # Extract video caption with multiple selectors
                        caption = "No caption"
                        caption_selectors = [
                            '[data-e2e="video-desc"] span',
                            '[data-e2e="video-desc"]',
                            '[data-e2e="browse-video-desc"]',
                            'h1[data-e2e="video-desc"]',
                            '.video-meta-caption',
                            '[class*="video-meta"] span',
                            '[class*="Caption"]',
                            '[class*="description"]',
                            'span[class*="SpanText"]'
                        ]
                        
                        for selector in caption_selectors:
                            try:
                                caption_element = await page.query_selector(selector)
                                if caption_element:
                                    caption_text = await caption_element.inner_text()
                                    if caption_text and caption_text.strip() and len(caption_text.strip()) > 2:
                                        caption = caption_text.strip()
                                        print(f"      📝 Found caption with selector: {selector}")
                                        break
                            except:
                                continue
                        
                        # If no caption found, try getting it from page content
                        if caption == "No caption":
                            try:
                                page_content = await page.content()
                                # Look for video description in the HTML
                                desc_match = re.search(r'"desc":"([^"]*)"', page_content)
                                if desc_match:
                                    caption = desc_match.group(1).replace('\\n', ' ').replace('\\', '')
                                    print(f"      📝 Found caption in page source")
                            except:
                                pass
                        
                        # Extract engagement metrics
                        views = "0"
                        likes = "0"
                        shares = "0"
                        
                        # Save video data
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
                        print(f"      ✅ Video: @{username} - {caption[:50]}...")
                        
                        # Extract comments
                        print(f"💬 Extracting comments...")
                        await extract_comments(page, video_url, all_comments)
                        
                        video_count += 1
                        
                        # Add delay between videos to avoid being blocked
                        await asyncio.sleep(2)
                        
                    except Exception as video_error:
                        print(f"      ❌ Error processing video: {video_error}")
                        continue
                
                print(f"✅ Completed #{clean_tag}: {video_count} videos processed")
                
            except Exception as e:
                print(f"⚠️ Error with hashtag #{tag}: {e}")
                continue

        # Check current directory
        current_dir = os.getcwd()
        print(f"\n📁 Current directory: {current_dir}")
        
        # Save videos to CSV
        if all_videos:
            videos_file = "tiktok_videos_detailed.csv"
            df_videos = pd.DataFrame(all_videos)
            df_videos.to_csv(videos_file, index=False)
            
            # Verify file was created
            if os.path.exists(videos_file):
                file_size = os.path.getsize(videos_file)
                print(f"✅ Video data saved to {videos_file} ({len(all_videos)} videos, {file_size} bytes)")
                print(f"   Full path: {os.path.abspath(videos_file)}")
            else:
                print(f"❌ Failed to create {videos_file}")
        else:
            print("❌ No video data to save")
        
        # Save comments to CSV
        if all_comments:
            comments_file = "tiktok_comments_detailed.csv"
            df_comments = pd.DataFrame(all_comments)
            df_comments.to_csv(comments_file, index=False)
            
            # Verify file was created
            if os.path.exists(comments_file):
                file_size = os.path.getsize(comments_file)
                print(f"✅ Comments saved to {comments_file} ({len(all_comments)} comments, {file_size} bytes)")
                print(f"   Full path: {os.path.abspath(comments_file)}")
            else:
                print(f"❌ Failed to create {comments_file}")
        else:
            print("❌ No comments to save")
        
        # Print summary
        print("\n📊 DETAILED SCRAPING SUMMARY:")
        print(f"   Total videos: {len(all_videos)}")
        print(f"   Total comments: {len(all_comments)}")
        print(f"   Unique users: {len(set([v['username'] for v in all_videos if v['username'] != 'Unknown']))}")
        print(f"   Videos with captions: {len([v for v in all_videos if v['caption'] != 'No caption'])}")
        
        # Show sample captions
        real_captions = [v['caption'] for v in all_videos if v['caption'] not in ['No caption', v['username']]]
        if real_captions:
            print(f"   Sample captions:")
            for cap in real_captions[:3]:
                print(f"     - {cap[:100]}...")

        await browser.close()

async def extract_comments(page, video_url, all_comments):
    """Extract comments from the current video page"""
    try:
        # Scroll down to load comments section
        print(f"        🔄 Scrolling to load comments...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        
        # Scroll a bit more to ensure comments are loaded
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(2000)
        
        # Try multiple comment selectors
        comment_selectors = [
            '[data-e2e="comment-level-1"]',
            '[data-e2e="comment-item"]',
            'div[class*="comment"]',
            'div[class*="Comment"]',
            '.comment-container',
            '[class*="CommentItemContainer"]'
        ]
        
        comments_found = []
        for selector in comment_selectors:
            try:
                comment_elements = await page.query_selector_all(selector)
                if comment_elements and len(comment_elements) > 0:
                    print(f"        ✅ Found {len(comment_elements)} comments with selector: {selector}")
                    comments_found = comment_elements
                    break
                else:
                    print(f"        ❌ No comments with selector: {selector}")
            except Exception as e:
                print(f"        ❌ Error with selector {selector}: {e}")
                continue
        
        if not comments_found:
            print(f"        ❌ No comments found with any selector")
            return
        
        # Extract comment data
        comment_count = 0
        for i, comment_element in enumerate(comments_found[:10]):  # Max 10 comments per video
            try:
                print(f"        🔍 Processing comment {i+1}...")
                
                # Get full comment HTML for debugging
                comment_html = await comment_element.inner_html()
                print(f"        📝 Comment HTML preview: {comment_html[:200]}...")
                
                # Get comment text with more aggressive selectors
                comment_text = ""
                text_selectors = [
                    '[data-e2e="comment-text"]',
                    'span[data-e2e="comment-text"]',
                    'p[data-e2e="comment-text"]',
                    'span[class*="text"]',
                    'p[class*="text"]',
                    'div[class*="text"]',
                    'span',
                    'p'
                ]
                
                for text_sel in text_selectors:
                    try:
                        text_elem = await comment_element.query_selector(text_sel)
                        if text_elem:
                            temp_text = await text_elem.inner_text()
                            if temp_text and temp_text.strip() and len(temp_text.strip()) > 3:
                                comment_text = temp_text.strip()
                                print(f"        📝 Found comment text with selector: {text_sel}")
                                break
                    except:
                        continue
                
                # If still no text, try getting all text from the element
                if not comment_text:
                    try:
                        all_text = await comment_element.inner_text()
                        if all_text and all_text.strip():
                            # Split by lines and take the longest meaningful line
                            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                            for line in lines:
                                if len(line) > 10 and not re.match(r'^\d+[smhd]?( ago)?$', line):
                                    comment_text = line
                                    break
                    except:
                        pass
                
                # Get comment author
                author = "Unknown"
                author_selectors = [
                    '[data-e2e="comment-author-nickname"]',
                    '[data-e2e="comment-username"]',
                    'span[class*="author"]',
                    'a[class*="author"]',
                    'span[class*="nickname"]',
                    'a[class*="nickname"]'
                ]
                
                for author_sel in author_selectors:
                    try:
                        author_elem = await comment_element.query_selector(author_sel)
                        if author_elem:
                            author_text = await author_elem.inner_text()
                            if author_text and author_text.strip():
                                author = author_text.strip()
                                break
                    except:
                        continue
                
                # Get comment likes
                likes = "0"
                try:
                    like_selectors = [
                        '[data-e2e="comment-like-count"]',
                        'span[class*="like"]',
                        'span[class*="count"]'
                    ]
                    for like_sel in like_selectors:
                        like_elem = await comment_element.query_selector(like_sel)
                        if like_elem:
                            like_text = await like_elem.inner_text()
                            if like_text and re.match(r'\d+', like_text):
                                likes = like_text
                                break
                except:
                    pass
                
                if comment_text and len(comment_text.strip()) > 3:
                    comment_data = {
                        "video_url": video_url,
                        "comment_author": author,
                        "comment_text": comment_text.strip(),
                        "comment_likes": likes
                    }
                    
                    all_comments.append(comment_data)
                    comment_count += 1
                    print(f"          ✅ Comment {comment_count}: @{author} - {comment_text[:50]}...")
                else:
                    print(f"          ❌ No valid comment text found")
                
            except Exception as comment_error:
                print(f" ❌ Error extracting comment {i+1}: {comment_error}")
                continue
        
        print(f"        ✅ Extracted {comment_count} comments total")
        
    except Exception as e:
        print(f"❌ Error extracting comments: {e}")

if __name__ == "__main__":
    asyncio.run(scrape_tiktok())