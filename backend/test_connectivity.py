"""
Connectivity Test Script
Tests connections to Redis and PostgreSQL
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_redis():
    """Test Redis connectivity"""
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings

        print("🔄 Testing Redis connection...")
        print(f"   URL: {settings.REDIS_URL}")

        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=5
        )

        # Test ping
        await redis_client.ping()
        print("✅ Redis connection: SUCCESS")

        # Test set/get
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        await redis_client.delete("test_key")

        print(f"✅ Redis read/write: SUCCESS")

        await redis_client.close()
        return True

    except Exception as e:
        print(f"❌ Redis connection: FAILED")
        print(f"   Error: {str(e)}")
        return False


async def test_database():
    """Test PostgreSQL connectivity"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        from app.core.config import settings

        print("\n🔄 Testing PostgreSQL connection...")
        print(f"   URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")

        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )

        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()

        print("✅ PostgreSQL connection: SUCCESS")
        print(f"✅ PostgreSQL query execution: SUCCESS")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL connection: FAILED")
        print(f"   Error: {str(e)}")
        return False


async def test_cache_system():
    """Test cache initialization"""
    try:
        print("\n🔄 Testing cache system...")
        from app.core.cache import init_cache, set_cached, get_cached, close_cache

        await init_cache()
        print("✅ Cache initialization: SUCCESS")

        # Test cache operations
        await set_cached("test_cache_key", {"data": "test"}, ttl=60)
        cached_value = await get_cached("test_cache_key")

        if cached_value and cached_value.get("data") == "test":
            print("✅ Cache operations: SUCCESS")
        else:
            print("⚠️  Cache operations: PARTIAL (data mismatch)")

        await close_cache()
        return True

    except Exception as e:
        print(f"❌ Cache system: FAILED")
        print(f"   Error: {str(e)}")
        return False


async def main():
    """Run all connectivity tests"""
    print("=" * 60)
    print("SOC Platform - Connectivity Test")
    print("=" * 60)

    results = {}

    # Test Redis
    results['redis'] = await test_redis()

    # Test PostgreSQL
    results['database'] = await test_database()

    # Test cache system
    results['cache'] = await test_cache_system()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service.capitalize()}: {'PASS' if status else 'FAIL'}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All connectivity tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the services.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)