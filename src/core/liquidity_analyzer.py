import logging
from typing import Dict, Optional

class LiquidityAnalyzer:
    """TOKEN SNIFFER - finds FRESH opportunities with high growth potential"""
    
    def __init__(self):
        # SNIFFER thresholds - prioritize fresh tokens over established ones
        self.min_liquidity_threshold = 500        # $500 minimum (catch very early)
        self.min_volume_threshold = 50            # $50 minimum (catch initial activity)
        self.min_confidence_score = 0.2           # Ultra low threshold for fresh tokens
        self.max_age_hours = 72                   # Only tokens < 72 hours old
        self.freshness_multiplier = 2.0           # Boost scores for fresh tokens
        
    async def analyze_pair(self, pair_data: Dict) -> Optional[Dict]:
        """Analyze pairs - prioritize FRESH tokens with growth potential"""
        try:
            liquidity = pair_data['total_liquidity_usd']
            volume = pair_data['volume_24h_usd']
            age_hours = pair_data.get('age_hours')
            
            # Basic filters - very permissive for fresh tokens
            if liquidity < self.min_liquidity_threshold:
                return None
            if volume < self.min_volume_threshold:
                return None
            
            # CRITICAL: Age filter - only fresh tokens
            if age_hours is not None and age_hours > self.max_age_hours:
                return None
            
            # Calculate scores with freshness bias
            opportunity_score = self._calculate_opportunity_score(pair_data)
            safety_score = self._calculate_safety_score(pair_data)
            momentum_score = self._calculate_momentum_score(pair_data)
            freshness_score = self._calculate_freshness_score(pair_data)
            
            # Apply freshness multiplier to opportunity score
            if age_hours is not None and age_hours <= 24:
                opportunity_score *= self.freshness_multiplier
            
            # Accept based on combined fresh + opportunity potential
            combined_score = (opportunity_score + freshness_score) / 2
            if combined_score >= self.min_confidence_score:
                alert_type = self._determine_alert_type(pair_data, opportunity_score, safety_score)
                
                return {
                    'pair_address': pair_data['pair_address'],
                    'alert_type': alert_type,
                    'opportunity_score': min(opportunity_score, 1.0),  # Cap at 1.0
                    'safety_score': safety_score,
                    'momentum_score': momentum_score,
                    'freshness_score': freshness_score,
                    'combined_score': combined_score,
                    'liquidity_usd': liquidity,
                    'volume_24h_usd': volume,
                    'base_symbol': pair_data['base_symbol'],
                    'quote_symbol': pair_data['quote_symbol'],
                    'dex_name': pair_data['dex_name'],
                    'price_usd': pair_data['price_usd'],
                    'market_cap_usd': pair_data['market_cap_usd'],
                    'txns_24h': pair_data['txns_24h'],
                    'age_hours': pair_data.get('age_hours'),
                    'volume_to_liquidity_ratio': pair_data.get('volume_to_liquidity_ratio', 0),
                    'price_change_24h': pair_data['price_change_24h'],
                    'reasoning': self._generate_reasoning(pair_data, opportunity_score, safety_score, momentum_score, freshness_score)
                }
            
            return None
            
        except Exception as e:
            return None
    
    def _calculate_opportunity_score(self, pair_data: Dict) -> float:
        """Calculate opportunity score - prioritize growth potential over size"""
        score = 0.0
        
        # Liquidity score (0-0.2) - Lower weight, focus on growth range
        liquidity = pair_data['total_liquidity_usd']
        if liquidity >= 100000:     # $100k+ (good for fresh tokens)
            score += 0.2
        elif liquidity >= 50000:    # $50k+ (growing)
            score += 0.18
        elif liquidity >= 25000:    # $25k+ (early growth)
            score += 0.15
        elif liquidity >= 10000:    # $10k+ (getting traction)
            score += 0.12
        elif liquidity >= 5000:     # $5k+ (initial liquidity)
            score += 0.08
        elif liquidity >= 1000:     # $1k+ (very early)
            score += 0.05
        
        # Volume score (0-0.3) - Higher weight for volume activity
        volume = pair_data['volume_24h_usd']
        if volume >= 500000:        # $500k+ (viral)
            score += 0.3
        elif volume >= 100000:      # $100k+ (trending)
            score += 0.25
        elif volume >= 50000:       # $50k+ (growing)
            score += 0.2
        elif volume >= 10000:       # $10k+ (active)
            score += 0.15
        elif volume >= 5000:        # $5k+ (getting noticed)
            score += 0.1
        elif volume >= 1000:        # $1k+ (early activity)
            score += 0.08
        elif volume >= 100:         # $100+ (initial trades)
            score += 0.05
        
        # Activity score (0-0.25) - Higher weight for transaction activity
        txns = pair_data['txns_24h']
        if txns >= 500:
            score += 0.25
        elif txns >= 200:
            score += 0.2
        elif txns >= 100:
            score += 0.15
        elif txns >= 50:
            score += 0.1
        elif txns >= 20:
            score += 0.08
        elif txns >= 10:
            score += 0.05
        
        # Volume-to-liquidity ratio bonus (0-0.25) - Key metric for momentum
        vol_to_liq = pair_data.get('volume_to_liquidity_ratio', 0)
        if vol_to_liq >= 10.0:      # Massive turnover (viral potential)
            score += 0.25
        elif vol_to_liq >= 5.0:     # Very high turnover
            score += 0.2
        elif vol_to_liq >= 2.0:     # High turnover
            score += 0.15
        elif vol_to_liq >= 1.0:     # Good turnover
            score += 0.1
        elif vol_to_liq >= 0.5:     # Moderate turnover
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_safety_score(self, pair_data: Dict) -> float:
        """Calculate safety score - adjusted for fresh tokens"""
        score = 0.0
        
        # Liquidity safety (0-0.4) - Lower thresholds for fresh tokens
        liquidity = pair_data['total_liquidity_usd']
        if liquidity >= 100000:     # $100k+ (safe for fresh)
            score += 0.4
        elif liquidity >= 50000:    # $50k+ (decent)
            score += 0.3
        elif liquidity >= 25000:    # $25k+ (moderate)
            score += 0.2
        elif liquidity >= 10000:    # $10k+ (minimum safe)
            score += 0.15
        elif liquidity >= 5000:     # $5k+ (risky but acceptable)
            score += 0.1
        elif liquidity >= 1000:     # $1k+ (very risky)
            score += 0.05
        
        # Volume consistency (0-0.3) - Regular activity is safer
        volume = pair_data['volume_24h_usd']
        if volume >= 100000:
            score += 0.3
        elif volume >= 50000:
            score += 0.25
        elif volume >= 10000:
            score += 0.2
        elif volume >= 5000:
            score += 0.15
        elif volume >= 1000:
            score += 0.1
        
        # Transaction spread (0-0.3) - More transactions = more distributed
        txns = pair_data['txns_24h']
        if txns >= 200:
            score += 0.3
        elif txns >= 100:
            score += 0.25
        elif txns >= 50:
            score += 0.2
        elif txns >= 20:
            score += 0.15
        elif txns >= 10:
            score += 0.1
        elif txns >= 5:
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_momentum_score(self, pair_data: Dict) -> float:
        """Calculate momentum score"""
        score = 0.0
        
        # Price change momentum
        price_change = pair_data['price_change_24h']
        if price_change > 100:      # 100%+ gain
            score += 0.5
        elif price_change > 50:     # 50%+ gain
            score += 0.3
        elif price_change > 20:     # 20%+ gain
            score += 0.2
        elif price_change > 10:     # 10%+ gain
            score += 0.1
        elif price_change > 0:      # Any gain
            score += 0.05
        
        # Volume momentum (high volume = momentum)
        vol_to_liq = pair_data.get('volume_to_liquidity_ratio', 0)
        if vol_to_liq >= 3.0:
            score += 0.3
        elif vol_to_liq >= 1.5:
            score += 0.2
        elif vol_to_liq >= 1.0:
            score += 0.1
        
        # Age momentum (newer = more momentum potential)
        age_hours = pair_data.get('age_hours')
        if age_hours is not None:
            if age_hours <= 1:      # Brand new
                score += 0.2
            elif age_hours <= 6:    # Very fresh
                score += 0.15
            elif age_hours <= 24:   # Fresh
                score += 0.1
            elif age_hours <= 72:   # Recent
                score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, pair_data: Dict) -> float:
        """Calculate freshness score - newer tokens get higher scores"""
        age_hours = pair_data.get('age_hours')
        if age_hours is None:
            return 0.1  # Unknown age gets low score
        
        score = 0.0
        
        # Age scoring - newer is better
        if age_hours <= 1:          # Brand new (< 1 hour)
            score += 0.5
        elif age_hours <= 6:        # Very fresh (< 6 hours)
            score += 0.4
        elif age_hours <= 12:       # Fresh (< 12 hours)
            score += 0.3
        elif age_hours <= 24:       # New (< 24 hours)
            score += 0.2
        elif age_hours <= 48:       # Recent (< 48 hours)
            score += 0.1
        elif age_hours <= 72:       # Still fresh (< 72 hours)
            score += 0.05
        
        # Momentum bonus for very new tokens with activity
        if age_hours <= 12:
            volume = pair_data['volume_24h_usd']
            if volume >= 10000:     # Good volume for new token
                score += 0.2
            elif volume >= 1000:    # Decent volume
                score += 0.1
        
        return min(score, 1.0)
    
    def _determine_alert_type(self, pair_data: Dict, opportunity: float, safety: float) -> str:
        """Determine alert type based on scores - prioritize freshness"""
        age_hours = pair_data.get('age_hours', 999)
        liquidity = pair_data['total_liquidity_usd']
        volume = pair_data['volume_24h_usd']
        vol_to_liq = pair_data.get('volume_to_liquidity_ratio', 0)
        
        # Prioritize by freshness and activity
        if age_hours <= 1:
            return "BRAND_NEW_LAUNCH"
        elif age_hours <= 6 and vol_to_liq >= 2.0:
            return "VIRAL_FRESH_TOKEN"
        elif age_hours <= 12 and volume >= 10000:
            return "TRENDING_NEW_TOKEN"
        elif age_hours <= 24:
            return "FRESH_LAUNCH"
        elif age_hours <= 48 and opportunity > 0.6:
            return "RECENT_OPPORTUNITY"
        elif vol_to_liq >= 5.0:
            return "HIGH_MOMENTUM_TOKEN"
        elif volume >= 50000:
            return "HIGH_VOLUME_OPPORTUNITY"
        else:
            return "EMERGING_OPPORTUNITY"
    
    def _generate_reasoning(self, pair_data: Dict, opportunity: float, safety: float, momentum: float, freshness: float) -> str:
        """Generate detailed reasoning focused on freshness and growth"""
        liquidity = pair_data['total_liquidity_usd']
        volume = pair_data['volume_24h_usd']
        txns = pair_data['txns_24h']
        price_change = pair_data['price_change_24h']
        age = pair_data.get('age_hours')
        vol_to_liq = pair_data.get('volume_to_liquidity_ratio', 0)
        
        # Focus on freshness and growth metrics
        freshness_level = "BRAND_NEW" if freshness > 0.7 else "VERY_FRESH" if freshness > 0.5 else "FRESH" if freshness > 0.3 else "RECENT"
        momentum_level = "VIRAL" if momentum > 0.8 else "HIGH" if momentum > 0.6 else "MEDIUM" if momentum > 0.4 else "LOW"
        
        age_str = f"{age:.1f}h old" if age is not None else "age unknown"
        
        # Highlight key sniffer metrics
        return f"{freshness_level} ({age_str}), ${liquidity:,.0f} liq, ${volume:,.0f} vol, {vol_to_liq:.1f}x turnover, {txns} txns, {price_change:+.1f}% 24h, {momentum_level} momentum"
