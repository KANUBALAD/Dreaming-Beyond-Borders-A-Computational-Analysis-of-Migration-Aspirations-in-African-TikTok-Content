import asyncio
from TikTokApi import TikTokApi
async def main():
    try:
        api = TikTokApi()
        
        # Test user lookup
        user = await api.user("therock")
        print(f"User: {user}")
        
        # Check what attributes are available
        if user:
            print(f"User attributes: {[attr for attr in dir(user) if not attr.startswith('_')]}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to install: pip install tiktokapipy")

if __name__ == "__main__":
    asyncio.run(main())