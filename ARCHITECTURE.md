# Waste Prediction Event Handler - Architecture Documentation

## Overview
This is a production-ready SQS event handler that processes waste prediction events using the `waste-predictor` library and persists results to MongoDB. The system follows a modular executor pattern for extensibility and maintainability.

## Architecture

### System Components

```
┌─────────────────┐
│   AWS SQS FIFO  │
│     Queue       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQS Handler    │
│  (sqs_handler)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Executor        │
│ Registry        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌──────────────┐
│ Event Executor  │──────▶│   MongoDB    │
│ (Waste Pred.)   │       │   Database   │
└─────────────────┘       └──────────────┘
```

### Project Structure

```
waste_prediction_event_handler/
├── sqs_handler.py              # Main SQS polling and message handling
├── database/
│   ├── __init__.py
│   └── connection.py           # MongoDB connection management
├── src/
│   ├── executors/              # Event executor pattern implementation
│   │   ├── __init__.py
│   │   ├── base_executor.py           # Abstract base class for all executors
│   │   ├── waste_prediction_executor.py  # Waste prediction implementation
│   │   └── executor_registry.py       # Factory for executor instantiation
│   └── utils/
│       └── logger_util.py      # Logging utilities
├── requirements.txt
└── README.md
```

## Key Components

### 1. SQS Handler (`sqs_handler.py`)
- **Purpose**: Poll SQS queue, receive messages, delegate to executors
- **Responsibilities**:
  - Initialize database connection on startup
  - Create executor registry
  - Long-poll SQS FIFO queue
  - Route events to appropriate executors
  - Handle DLQ for failed messages
  - Graceful shutdown and resource cleanup

### 2. Executor Registry (`src/executors/executor_registry.py`)
- **Pattern**: Factory Pattern
- **Purpose**: Map event names to executor implementations
- **Features**:
  - Dynamic executor registration
  - Event name validation
  - Executor instantiation with DB client injection

**Supported Events:**
- `WastePredictionEvent` → `WastePredictionExecutor`
- `waste_prediction` → `WastePredictionExecutor`

### 3. Base Executor (`src/executors/base_executor.py`)
- **Pattern**: Template Method Pattern
- **Purpose**: Define contract and common behavior for all executors
- **Methods**:
  - `execute()`: Abstract method for business logic
  - `save_to_database()`: Abstract method for persistence
  - `process()`: Template method orchestrating execution + persistence

### 4. Waste Prediction Executor (`src/executors/waste_prediction_executor.py`)
- **Purpose**: Handle waste prediction events
- **Process**:
  1. Validate input parameters
  2. Call `waste-predictor` library
  3. Save prediction results to MongoDB
- **Database**: 
  - Database: `waste_management`
  - Collection: `waste_predictions`

## Data Flow

### 1. Message Receipt
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

### 2. Processing
1. SQS handler receives message
2. Parse JSON payload
3. Extract `eventName` and `eventData`
4. Registry returns appropriate executor
5. Executor validates parameters
6. Executor calls `predict_waste()` from library
7. Result saved to MongoDB

### 3. Database Document Structure
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

## Configuration

### Environment Variables (.env)
```bash
# AWS SQS Configuration
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/waste-prediction.fifo
DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789/waste-prediction-dlq.fifo
AWS_REGION=us-east-1

# SQS Polling Configuration
POLL_WAIT=20          # Long polling wait time in seconds
MAX_MESSAGES=10       # Max messages per batch

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017/
```

## Adding New Event Types

### Step 1: Create New Executor
```python
# src/executors/my_new_executor.py
from .base_executor import BaseExecutor

class MyNewExecutor(BaseExecutor):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.db = db_client.get_database("my_database")
        self.collection = self.db.get_collection("my_collection")
    
    def execute(self, event_data):
        # Your business logic here
        result = perform_operation(event_data)
        return result
    
    def save_to_database(self, event_data, result):
        # Save to MongoDB
        self.collection.insert_one({
            "timestamp": datetime.utcnow(),
            "data": event_data,
            "result": result
        })
```

### Step 2: Register in Executor Registry
```python
# src/executors/executor_registry.py
from .my_new_executor import MyNewExecutor

class ExecutorRegistry:
    def __init__(self, db_client):
        self._executor_map = {
            "WastePredictionEvent": WastePredictionExecutor,
            "MyNewEvent": MyNewExecutor,  # Add here
        }
```

### Step 3: Update __init__.py
```python
# src/executors/__init__.py
from .my_new_executor import MyNewExecutor

__all__ = [..., "MyNewExecutor"]
```

## Error Handling

### 1. Validation Errors
- Missing parameters → ValueError with details
- Invalid event name → ValueError listing valid events

### 2. Processing Errors
- All exceptions logged with full traceback
- Message sent to DLQ
- Original message deleted from queue

### 3. Database Errors
- Connection failure → Startup fails with error
- Write failure → Logged, message goes to DLQ

## Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file with required variables (see Configuration section)

### 3. Start the Handler
```bash
python sqs_handler.py
```

### 4. Graceful Shutdown
Press `Ctrl+C` to trigger graceful shutdown:
- Stops polling
- Closes database connection
- Logs shutdown event

## Monitoring & Logging

### Log Levels
- `INFO`: Normal operations (message received, processed, deleted)
- `DEBUG`: Detailed event data
- `ERROR`: Processing failures, DLQ operations
- `WARNING`: Non-critical issues (DLQ send failures)

### Key Metrics to Monitor
- Messages processed per minute
- Average processing time
- DLQ message count
- Database write latency
- Executor success/failure rates

## Production Best Practices

✅ **Implemented:**
- Database connection pooling (MongoDB client)
- Environment-based configuration
- Structured logging
- Error handling and DLQ
- Graceful shutdown
- Modular, extensible architecture
- Parameter validation

🔄 **Recommended Additions:**
- Health check endpoint
- Prometheus metrics
- Distributed tracing (OpenTelemetry)
- Circuit breaker for external dependencies
- Retry logic with exponential backoff
- Connection pooling configuration
- Docker containerization

## Security Considerations

- AWS credentials via IAM roles (recommended) or environment variables
- MongoDB connection string in .env (never commit)
- Use AWS Secrets Manager for production credentials
- Enable MongoDB authentication
- Implement message encryption for sensitive data
- Validate and sanitize all input data

## Testing

### Unit Tests
Test individual executors:
```python
def test_waste_prediction_executor():
    mock_db = MockMongoClient()
    executor = WastePredictionExecutor(mock_db)
    result = executor.execute({
        "production_volume": 50000,
        "rain_sum": 200,
        # ... other params
    })
    assert result["Total_Waste_kg"] > 0
```

### Integration Tests
Test with real SQS and MongoDB (test environment)

### Local Development
Use LocalStack for SQS and MongoDB container for database

## License & Support

For questions or issues, contact the development team.
