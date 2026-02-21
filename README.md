# Waste Prediction Event Handler

A production-ready, modular SQS FIFO event handler that processes waste prediction events using the `waste-predictor` library and persists results to MongoDB.

## 🚀 Features

- ✅ **Production-Ready Architecture** - Modular executor pattern for extensibility
- ✅ **Event-Driven Processing** - Polls AWS SQS FIFO queue for events
- ✅ **Database Persistence** - Automatic MongoDB storage of predictions
- ✅ **Error Handling** - Dead Letter Queue (DLQ) for failed messages
- ✅ **Graceful Shutdown** - Proper resource cleanup on termination
- ✅ **Structured Logging** - Comprehensive logging for monitoring
- ✅ **Type Safe** - Type hints and validation throughout

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Event Format](#-event-format)
- [Adding New Event Types](#-adding-new-event-types)
- [Monitoring](#-monitoring)
- [Production Deployment](#-production-deployment)

## 🏗 Architecture

```
┌─────────────────┐
│   AWS SQS FIFO  │  ← Events arrive here
│     Queue       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQS Handler    │  ← Polls and routes events
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Executor        │  ← Factory pattern for event routing
│ Registry        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌──────────────┐
│ Waste Prediction│──────▶│   MongoDB    │  ← Results persisted
│   Executor      │       │   Database   │
└─────────────────┘       └──────────────┘
```

**Key Components:**
- **Executor Registry**: Maps event names to handler implementations
- **Base Executor**: Abstract class defining executor contract
- **Waste Prediction Executor**: Implements waste prediction logic
- **Database Layer**: MongoDB connection and persistence

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# AWS SQS Configuration
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/waste-prediction.fifo
DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789/waste-prediction-dlq.fifo
AWS_REGION=us-east-1

# SQS Polling Configuration
POLL_WAIT=20
MAX_MESSAGES=10

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017/
```

### 3. Verify Configuration

```bash
python check_config.py
```

This will validate:
- ✅ Environment variables are set
- ✅ Python packages are installed
- ✅ AWS credentials are configured
- ✅ SQS queue is accessible
- ✅ MongoDB connection works

### 4. Start the Handler

```bash
python sqs_handler.py
```

The handler will:
1. Connect to MongoDB
2. Initialize executor registry
3. Start polling SQS queue
4. Process events and save results to database

### 5. Send Test Events

```bash
python send_test_message.py
```

## ⚙ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SQS_QUEUE_URL` | ✅ Yes | - | SQS FIFO queue URL to poll |
| `DLQ_URL` | ✅ Yes | - | Dead letter queue URL for failed messages |
| `MONGODB_URL` | ✅ Yes | - | MongoDB connection string |
| `AWS_REGION` | ❌ No | `us-east-1` | AWS region for SQS |
| `POLL_WAIT` | ❌ No | `20` | Long polling wait time (seconds) |
| `MAX_MESSAGES` | ❌ No | `10` | Max messages per batch |

### AWS Credentials

Configure AWS credentials using one of these methods:

1. **AWS CLI** (Recommended for local development):
   ```bash
   aws configure
   ```

2. **Environment Variables**:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

3. **IAM Role** (Recommended for production on EC2/ECS)

## 📝 Usage

### Event Format

Send messages to SQS with this JSON structure:

```json
{
  "eventName": "WastePredictionEvent",
  "eventData": {
    "production_volume": 50000,
    "rain_sum": 200,
    "temperature_mean": 28,
    "humidity_mean": 85,
    "wind_speed_mean": 15,
    "month": 6
  }
}
```

### Supported Events

| Event Name | Executor | Description |
|------------|----------|-------------|
| `WastePredictionEvent` | `WastePredictionExecutor` | Predicts waste based on production and weather data |
| `waste_prediction` | `WastePredictionExecutor` | Alias for WastePredictionEvent |

### Database Storage

Results are stored in MongoDB:

**Database**: `waste_management`  
**Collection**: `waste_predictions`

Example document:
```json
{
  "_id": ObjectId("..."),
  "timestamp": "2026-02-21T10:30:00Z",
  "input_parameters": {
    "production_volume": 50000,
    "rain_sum": 200,
    "temperature_mean": 28,
    "humidity_mean": 85,
    "wind_speed_mean": 15,
    "month": 6
  },
  "prediction_result": {
    "total_waste_kg": 101805.0
  },
  "metadata": {
    "event_type": "waste_prediction",
    "processor_version": "1.0.0"
  }
}
```

## 🔧 Adding New Event Types

### 1. Create New Executor

```python
# src/executors/my_executor.py
from .base_executor import BaseExecutor
from datetime import datetime

class MyExecutor(BaseExecutor):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = db_client.waste_management.my_collection
    
    def execute(self, event_data):
        # Your business logic
        result = {"status": "processed"}
        return result
    
    def save_to_database(self, event_data, result):
        self.collection.insert_one({
            "timestamp": datetime.utcnow(),
            "data": event_data,
            "result": result
        })
```

### 2. Register in Executor Registry

```python
# src/executors/executor_registry.py
from .my_executor import MyExecutor

class ExecutorRegistry:
    def __init__(self, db_client):
        self._executor_map = {
            "WastePredictionEvent": WastePredictionExecutor,
            "MyNewEvent": MyExecutor,  # Add here
        }
```

### 3. Update Package Exports

```python
# src/executors/__init__.py
from .my_executor import MyExecutor
__all__ = [..., "MyExecutor"]
```

## 📊 Monitoring

### Log Levels

The handler produces structured logs:

- `INFO`: Normal operations (messages received, processed, deleted)
- `DEBUG`: Detailed event data
- `ERROR`: Processing failures, DLQ operations
- `WARNING`: Non-critical issues

### Key Metrics to Monitor

- Messages processed per minute
- DLQ message count
- Database write latency
- Executor success/failure rates
- Average processing time

### Health Checks

Monitor these indicators:
- SQS approximate message count
- DLQ depth (should be near zero)
- Database connection status
- Process uptime

## 🚢 Production Deployment

### Recommended Setup

1. **Containerization** - Deploy using Docker
2. **Orchestration** - Use ECS Fargate or Kubernetes
3. **Auto-scaling** - Scale based on SQS queue depth
4. **Monitoring** - CloudWatch + Prometheus + Grafana
5. **Secrets** - AWS Secrets Manager for credentials
6. **Logging** - CloudWatch Logs or ELK stack

### Docker Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "sqs_handler.py"]
```

### Graceful Shutdown

The handler supports graceful shutdown on `Ctrl+C`:
- Stops polling new messages
- Finishes processing current messages
- Closes database connection
- Logs shutdown event

## 🔒 Security Best Practices

- ✅ Use IAM roles instead of access keys in production
- ✅ Store secrets in AWS Secrets Manager or Parameter Store
- ✅ Enable MongoDB authentication
- ✅ Use VPC endpoints for SQS access
- ✅ Validate and sanitize all input data
- ✅ Enable encryption at rest and in transit
- ✅ Use least-privilege IAM policies

## 📁 Project Structure

```
waste_prediction_event_handler/
├── sqs_handler.py              # Main application entry point
├── send_test_message.py        # Test event sender utility
├── check_config.py             # Configuration validator
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── ARCHITECTURE.md             # Detailed architecture docs
├── database/
│   ├── __init__.py
│   └── connection.py           # MongoDB connection
└── src/
    ├── executors/              # Event executor pattern
    │   ├── __init__.py
    │   ├── base_executor.py           # Abstract base class
    │   ├── waste_prediction_executor.py  # Waste prediction logic
    │   └── executor_registry.py       # Event routing factory
    └── utils/
        └── logger_util.py      # Logging configuration
```

## 🛠 Development

### Running Tests

```bash
# Unit tests
pytest tests/

# Integration tests (requires test infrastructure)
pytest tests/integration/
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
pylint src/

# Formatting
black src/
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📧 Support

For issues or questions, create an issue in the repository.

---

Built with ❤️ for efficient waste prediction processing
