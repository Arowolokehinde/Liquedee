#!/usr/bin/env python3
"""
Quick start script for Liquidity Sniffer Agent
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.runner import main

if __name__ == "__main__":
    print("🚀 Starting Liquidity Sniffer Agent...")
    print("📊 Monitoring Solana pairs for high liquidity opportunities...")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown complete. Goodbye!")