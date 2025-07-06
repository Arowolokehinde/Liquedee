# Liquedee - Cryptocurrency Liquidity Analysis Platform

A comprehensive cryptocurrency liquidity analysis and token discovery platform built for Solana and multi-chain environments. Features real-time monitoring, ML-powered scoring, and automated Telegram alerts for emerging opportunities.

## 🚀 Features

### Core Functionality
- **Real-time Liquidity Monitoring**: Track token pairs across multiple DEXs
- **Alpha Scanner**: Multi-chain trending token discovery with social sentiment analysis
- **Gem Hunter**: Specialized scanner for early-stage tokens with strict filtering criteria
- **ML-Powered Analysis**: Machine learning models for opportunity scoring and risk assessment
- **Telegram Bot Integration**: Automated alerts and interactive bot commands
- **Multi-chain Support**: Solana, Ethereum, BSC, Polygon, Arbitrum, Avalanche, and Base

### Advanced Features
- **Real-time WebSocket Monitoring**: Live price and volume tracking
- **Machine Learning Models**: XGBoost and TensorFlow integration with MLflow tracking
- **Database Persistence**: PostgreSQL with SQLAlchemy ORM
- **Caching Layer**: Redis for performance optimization
- **Background Tasks**: Celery for asynchronous processing
- **Comprehensive Testing**: pytest with async support and coverage reporting

## 🏗️ Architecture

```
liquedee/
├── src/
│   ├── core/                    # Core scanning and analysis engines
│   │   ├── alpha_scanner.py     # Multi-chain trending token scanner
│   │   ├── gem_hunter.py        # Specialized gem discovery
│   │   ├── liquidity_analyzer.py # Liquidity analysis and scoring
│   │   ├── realtime_sniffer.py  # Real-time monitoring
│   │   └── solana_client.py     # Solana blockchain integration
│   ├── api/                     # FastAPI REST endpoints
│   ├── database/                # Database models and setup
│   ├── ml/                      # Machine learning models
│   ├── telegram_bot/            # Telegram bot implementation
│   └── monitoring/              # System monitoring and health checks
├── config/                      # Configuration management
├── scripts/                     # Utility scripts
├── test/                        # Test suites
└── docker/                      # Docker configuration
```

## 🔧 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Node.js (for some dependencies)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/liquedee.git
   cd liquedee
   ```

2. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -m src.database.setup
   ```

### Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE liquidity_db;
   CREATE USER liquidity_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE liquidity_db TO liquidity_user;
   ```

3. **Configure Redis**
   ```bash
   redis-server
   ```

4. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://liquidity_user:your_secure_password@localhost:5432/liquidity_db"
   export REDIS_URL="redis://localhost:6379/0"
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

## 📊 Usage

### Running the Core Scanners

#### Alpha Scanner
```bash
python -m src.core.alpha_scanner
```
- Scans for trending tokens across multiple chains
- Minimum volume: $50k, Market cap: $100k
- Tracks social mentions and price momentum

#### Gem Hunter
```bash
python -m src.core.gem_hunter
```
- Finds early-stage tokens with strict criteria
- Age: <72 hours, Liquidity: ≥$2k
- Volume spike: ≥200% increase

#### Real-time Sniffer
```bash
python -m src.core.realtime_sniffer
```
- Continuous monitoring of liquidity changes
- WebSocket connections for live data
- Automated alert generation

### Telegram Bot

1. **Start the bot**
   ```bash
   python scripts/run_bot.py
   ```

2. **Available commands**
   - `/start` - Initialize bot
   - `/scan` - Manual scan for opportunities
   - `/quick` - Quick liquidity check
   - `/subscribe` - Subscribe to alerts
   - `/settings` - Configure preferences

### API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Access the API documentation at `http://localhost:8000/docs`

## 🤖 Machine Learning

### Model Training
```bash
python -m src.ml.train_models
```

### Supported Models
- **XGBoost**: Opportunity scoring and risk assessment
- **TensorFlow**: Deep learning for pattern recognition
- **MLflow**: Experiment tracking and model versioning

### Model Features
- Liquidity metrics
- Volume patterns
- Price momentum
- Social sentiment
- Market cap trends

## 📈 Monitoring

### System Health
```bash
python -m src.monitoring.health_check
```

### Metrics Collection
- Prometheus metrics exposed on `/metrics`
- Grafana dashboards for visualization
- Sentry integration for error tracking

### Logging
- Structured logging with loguru
- Configurable log levels
- Centralized log aggregation

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/liquidity_db
REDIS_URL=redis://localhost:6379/0

# Blockchain
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WSS_URL=wss://api.mainnet-beta.solana.com

# APIs
DEXSCREENER_BASE_URL=https://api.dexscreener.com/latest
JUPITER_BASE_URL=https://quote-api.jup.ag/v6

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# ML
MLFLOW_TRACKING_URI=http://localhost:5000
```

### Scanner Configuration
Edit `config/settings.py` to customize:
- Minimum liquidity thresholds
- Volume spike detection
- Age filters for gem hunting
- Alert frequency and criteria

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run specific test suites
```bash
pytest test/test_alpha_scanner.py
pytest test/test_gem_hunter.py
pytest test/test_realtime_system.py
```

### Coverage report
```bash
pytest --cov=src --cov-report=html
```

## 🚀 Deployment

### Production Deployment
1. **Configure environment for production**
   ```bash
   export DEBUG=False
   export API_WORKERS=4
   ```

2. **Use production database**
   ```bash
   export DATABASE_URL="postgresql://prod_user:prod_pass@prod_host:5432/prod_db"
   ```

3. **Deploy with Docker**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Cloud Deployment
- **Render**: Configuration in `render.yaml`
- **AWS**: ECS/Fargate ready
- **Google Cloud**: Cloud Run compatible

## 📋 API Reference

### Core Endpoints

#### GET /api/v1/scan/alpha
Scan for alpha opportunities
```json
{
  "max_results": 20,
  "min_volume": 50000,
  "chains": ["solana", "ethereum"]
}
```

#### GET /api/v1/scan/gems
Hunt for early-stage gems
```json
{
  "max_age_hours": 72,
  "min_liquidity": 2000,
  "max_results": 15
}
```

#### GET /api/v1/pairs/{pair_address}
Get detailed pair information
```json
{
  "pair_address": "string",
  "liquidity_usd": 0,
  "volume_24h": 0,
  "price_change_24h": 0
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run linting
black src/
isort src/
flake8 src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Cryptocurrency trading involves significant risk, and you should never invest more than you can afford to lose. The authors are not responsible for any financial losses incurred through the use of this software.

## 🔗 Links

- [Documentation](https://docs.liquedee.com)
- [API Reference](https://api.liquedee.com/docs)
- [Discord Community](https://discord.gg/liquedee)
- [Twitter](https://twitter.com/liquedee)

## 🙏 Acknowledgments

- [DexScreener](https://dexscreener.com) for DEX data
- [Jupiter](https://jup.ag) for Solana price feeds
- [Solana Labs](https://solana.com) for blockchain infrastructure
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
