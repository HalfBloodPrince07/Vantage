import sys
import os
import asyncio
import traceback

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.memory.memory_manager import MemoryManager

async def test_memory_init():
    print("Testing MemoryManager initialization...")
    try:
        # Use default config values
        manager = MemoryManager(
            redis_url="redis://localhost:6379",
            database_url="sqlite+aiosqlite:///locallens_memory.db"
        )
        await manager.initialize()
        print("✅ Initialization successful")
        await manager.close()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_memory_init())
