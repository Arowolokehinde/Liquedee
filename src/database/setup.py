import asyncio

import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

from .models import Base


async def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database first
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="liquidity_user",
            password="your_secure_password",
            database="postgres",
        )

        # Check if our database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'liquidity_db'"
        )

        if not result:
            await conn.execute("CREATE DATABASE liquidity_db")
            print("✅ Created liquidity_db database")
        else:
            print("✅ Database liquidity_db already exists")

        await conn.close()
    except Exception as e:
        print(f"❌ Database creation error: {e}")


def create_tables():
    """Create all tables"""
    try:
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(engine)
        print("✅ Created all database tables")
    except Exception as e:
        print(f"❌ Table creation error: {e}")


async def setup_database():
    """Complete database setup"""
    print("🔧 Setting up database...")
    await create_database()
    create_tables()
    print("🎉 Database setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_database())
