from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()

class TokenPair(Base):
    """Core token pair information"""
    __tablename__ = "token_pairs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_address = Column(String(44), unique=True, nullable=False)
    base_token = Column(String(44), nullable=False)  # Token address
    quote_token = Column(String(44), nullable=False)  # Usually SOL
    base_symbol = Column(String(20), nullable=False)
    quote_symbol = Column(String(20), nullable=False)
    dex_name = Column(String(50), nullable=False)  # Raydium, Orca, etc.
    pool_address = Column(String(44), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_pair_address', 'pair_address'),
        Index('idx_base_token', 'base_token'),
        Index('idx_created_at', 'created_at'),
    )

class LiquiditySnapshot(Base):
    """Real-time liquidity data snapshots"""
    __tablename__ = "liquidity_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_address = Column(String(44), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Liquidity metrics
    total_liquidity_usd = Column(Float, nullable=False)
    base_liquidity = Column(Float, nullable=False)
    quote_liquidity = Column(Float, nullable=False)
    
    # Volume and price data
    volume_24h_usd = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    
    # Trading metrics
    txns_24h = Column(Integer, nullable=True)
    buyers_24h = Column(Integer, nullable=True)
    sellers_24h = Column(Integer, nullable=True)
    
    # Risk indicators
    fdv_usd = Column(Float, nullable=True)  # Fully Diluted Valuation
    market_cap_usd = Column(Float, nullable=True)
    
    # Raw data for ML features
    raw_data = Column(JSONB, nullable=True)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_pair_timestamp', 'pair_address', 'timestamp'),
        Index('idx_liquidity_usd', 'total_liquidity_usd'),
        Index('idx_timestamp', 'timestamp'),
    )

class PairAlert(Base):
    """Generated alerts for high-liquidity pairs"""
    __tablename__ = "pair_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_address = Column(String(44), nullable=False)
    alert_type = Column(String(50), nullable=False)  # 'high_liquidity', 'volume_spike', etc.
    confidence_score = Column(Float, nullable=False)
    
    # Alert data
    triggered_at = Column(DateTime, default=datetime.utcnow)
    liquidity_usd = Column(Float, nullable=False)
    volume_24h_usd = Column(Float, nullable=True)
    
    # Status tracking
    is_processed = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    
    # Additional context
    alert_data = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_triggered_at', 'triggered_at'),
        Index('idx_confidence_score', 'confidence_score'),
    )

class TradeSimulation(Base):
    """Simulated trade results for learning"""
    __tablename__ = "trade_simulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pair_address = Column(String(44), nullable=False)
    simulation_time = Column(DateTime, default=datetime.utcnow)
    
    # Trade parameters
    trade_amount_usd = Column(Float, nullable=False)
    expected_slippage = Column(Float, nullable=False)
    actual_slippage = Column(Float, nullable=True)
    
    # Results
    predicted_price = Column(Float, nullable=False)
    actual_price = Column(Float, nullable=True)
    profit_loss_usd = Column(Float, nullable=True)
    
    # Learning data
    features_used = Column(JSONB, nullable=True)
    model_version = Column(String(50), nullable=True)
    
    __table_args__ = (
        Index('idx_simulation_time', 'simulation_time'),
        Index('idx_pair_simulation', 'pair_address', 'simulation_time'),
    )