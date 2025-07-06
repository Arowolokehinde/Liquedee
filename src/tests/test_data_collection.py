import asyncio

import pytest

from src.core.dexscreener import DexScreenerClient
from src.core.liquidity_analyzer import LiquidityAnalyzer
from src.core.solana_client import SolanaClient


class TestDataCollection:
    """Test suite for data collection components"""

    @pytest.fixture
    def dexscreener_client(self):
        return DexScreenerClient()

    @pytest.fixture
    def solana_client(self):
        return SolanaClient()

    @pytest.fixture
    def analyzer(self):
        return LiquidityAnalyzer()

    async def test_dexscreener_connection(self, dexscreener_client):
        """Test DexScreener API connection"""
        pairs = await dexscreener_client.get_latest_pairs()
        assert isinstance(pairs, list)
        assert len(pairs) > 0

        # Test first pair parsing
        if pairs:
            parsed = dexscreener_client.parse_pair_data(pairs[0])
            assert parsed is not None
            assert "pair_address" in parsed
            assert "total_liquidity_usd" in parsed

    async def test_solana_connection(self, solana_client):
        """Test Solana RPC connection"""
        # Test with a known Solana address (SOL token)
        sol_mint = "So11111111111111111111111111111111111111112"
        supply_info = await solana_client.get_token_supply(sol_mint)
        assert supply_info is not None
        assert "amount" in supply_info

    async def test_liquidity_analyzer(self, analyzer):
        """Test liquidity analysis"""
        # Mock high liquidity pair data
        mock_pair = {
            "pair_address": "test_address",
            "base_symbol": "TEST",
            "quote_symbol": "SOL",
            "dex_name": "raydium",
            "total_liquidity_usd": 150000,
            "volume_24h_usd": 75000,
            "txns_24h": 500,
            "price_change_24h": 5.2,
        }

        alert = await analyzer.analyze_pair(mock_pair)
        assert alert is not None
        assert alert["alert_type"] == "high_liquidity"
        assert alert["confidence_score"] > 0.7

    async def test_data_flow(self, dexscreener_client, analyzer):
        """Test complete data flow"""
        # Get real pair data
        pairs = await dexscreener_client.get_latest_pairs()
        if pairs:
            parsed_pair = dexscreener_client.parse_pair_data(pairs[0])
            if parsed_pair:
                # Test analysis
                alert = await analyzer.analyze_pair(parsed_pair)
                # Alert may be None if pair doesn't meet criteria
                if alert:
                    assert "pair_address" in alert
                    assert "confidence_score" in alert
