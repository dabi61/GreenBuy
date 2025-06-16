import asyncio
import logging
from api.auth.token_blacklist import cleanup_blacklist

logger = logging.getLogger(__name__)

async def cleanup_blacklist_periodically():
    """
    Background task để cleanup token blacklist mỗi 1 giờ
    """
    while True:
        try:
            cleanup_blacklist()
            logger.info("Token blacklist cleanup completed")
        except Exception as e:
            logger.error(f"Error during token blacklist cleanup: {e}")
        
        # Chờ 1 giờ trước khi cleanup tiếp theo
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour

def start_background_tasks():
    """
    Khởi động các background tasks
    """
    asyncio.create_task(cleanup_blacklist_periodically()) 