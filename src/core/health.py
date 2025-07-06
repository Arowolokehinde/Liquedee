import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncpg
import redis  # Use sync redis for now
from config.settings import settings

async def check_database():
    """Test PostgreSQL connection"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        await conn.execute('SELECT 1')
        await conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def check_redis():
    """Test Redis connection"""
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        r.close()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

async def health_check():
    """Run all health checks"""
    print("🔍 Running health checks...")
    
    db_ok = await check_database()
    redis_ok = await check_redis()
    
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Redis: {'✅' if redis_ok else '❌'}")
    
    if db_ok and redis_ok:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some systems need attention")
    
    return db_ok and redis_ok

if __name__ == "__main__":
    asyncio.run(health_check())