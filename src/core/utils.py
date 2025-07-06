import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates incoming data for quality and completeness"""
    
    @staticmethod
    def validate_pair_data(pair_data: Dict) -> bool:
        """Validate pair data completeness"""
        required_fields = [
            'pair_address', 'base_token', 'quote_token',
            'base_symbol', 'quote_symbol', 'total_liquidity_usd'
        ]
        
        for field in required_fields:
            if field not in pair_data or pair_data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate addresses (basic check)
        if len(pair_data['pair_address']) != 44:
            logger.warning(f"Invalid pair address length: {pair_data['pair_address']}")
            return False
        
        # Validate liquidity is positive
        if pair_data['total_liquidity_usd'] <= 0:
            logger.warning(f"Invalid liquidity amount: {pair_data['total_liquidity_usd']}")
            return False
        
        return True
    
    @staticmethod
    def sanitize_pair_data(pair_data: Dict) -> Dict:
        """Sanitize and normalize pair data"""
        sanitized = pair_data.copy()
        
        # Ensure numeric fields are properly typed
        numeric_fields = [
            'total_liquidity_usd', 'base_liquidity', 'quote_liquidity',
            'volume_24h_usd', 'price_usd', 'price_change_24h',
            'fdv_usd', 'market_cap_usd'
        ]
        
        for field in numeric_fields:
            if field in sanitized:
                try:
                    sanitized[field] = float(sanitized[field]) if sanitized[field] else 0.0
                except (ValueError, TypeError):
                    sanitized[field] = 0.0
        
        # Ensure integer fields
        integer_fields = ['txns_24h', 'buyers_24h', 'sellers_24h']
        for field in integer_fields:
            if field in sanitized:
                try:
                    sanitized[field] = int(sanitized[field]) if sanitized[field] else 0
                except (ValueError, TypeError):
                    sanitized[field] = 0
        
        return sanitized

class PerformanceMonitor:
    """Monitors system performance and collection metrics"""
    
    def __init__(self):
        self.metrics = {
            'pairs_processed': 0,
            'alerts_generated': 0,
            'api_calls': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
    
    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a performance metric"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
    
    def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        uptime = datetime.utcnow() - self.metrics['start_time']
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'pairs_processed': self.metrics['pairs_processed'],
            'alerts_generated': self.metrics['alerts_generated'],
            'api_calls': self.metrics['api_calls'],
            'errors': self.metrics['errors'],
            'pairs_per_minute': self.metrics['pairs_processed'] / max(uptime.total_seconds() / 60, 1),
            'error_rate': self.metrics['errors'] / max(self.metrics['pairs_processed'], 1)
        }
    
    def log_performance(self):
        """Log current performance metrics"""
        summary = self.get_performance_summary()
        logger.info(f"📊 Performance Summary:")
        logger.info(f"   ⏱️  Uptime: {summary['uptime_seconds']:.0f}s")
        logger.info(f"   📈 Pairs processed: {summary['pairs_processed']}")
        logger.info(f"   🚨 Alerts generated: {summary['alerts_generated']}")
        logger.info(f"   📞 API calls: {summary['api_calls']}")
        logger.info(f"   ❌ Errors: {summary['errors']}")
        logger.info(f"   🔄 Rate: {summary['pairs_per_minute']:.1f} pairs/min")

class ConfigManager:
    """Manages dynamic configuration updates"""
    
    def __init__(self):
        self.config = {
            'collection_interval': 30,
            'min_liquidity_threshold': 10000,
            'high_liquidity_threshold': 100000,
            'volume_spike_threshold': 50000,
            'max_pairs_per_cycle': 1000,
            'alert_cooldown_minutes': 5
        }
    
    def update_config(self, updates: Dict):
        """Update configuration parameters"""
        for key, value in updates.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                logger.info(f"⚙️  Config updated: {key} = {value} (was {old_value})")
    
    def get_config(self, key: str = None):
        """Get configuration value(s)"""
        if key:
            return self.config.get(key)
        return self.config.copy()