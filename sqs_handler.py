import os
import time
import json
import logging
import uuid
from dotenv import load_dotenv, find_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from src.utils.logger_util import logger
from src.executors.executor_registry import ExecutorRegistry
from database.connection import get_mongo_client

# load .env if present
if load_dotenv:
    load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
DLQ_URL = os.getenv("DLQ_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
POLL_WAIT = int(os.getenv("POLL_WAIT", "20"))
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "10"))


def send_to_dlq(sqs_client, dlq_url: str, body: str, attributes: dict | None = None):
    try:
        params = {
            "QueueUrl": dlq_url,
            "MessageBody": body,
            "MessageGroupId": (
                attributes.get("MessageGroupId", "dlq-group")
                if attributes
                else "dlq-group"
            ),
            "MessageDeduplicationId": str(uuid.uuid4()),
        }
        sqs_client.send_message(**params)
        logger.info("Sent message to DLQ")
    except (BotoCoreError, ClientError) as e:
        logger.error("Failed to send to DLQ: %s", e)


def process_message(executor_registry: ExecutorRegistry, message: dict, sqs_client, queue_url: str):
    body = message.get("Body")
    receipt_handle = message.get("ReceiptHandle")
    message_id = message.get("MessageId")

    logger.info("Processing message %s", message_id)
    try:
        payload = json.loads(body) # type: ignore

        event_name = payload.get("eventName")
        event_data = payload.get("eventData")

        if not event_name:
            raise ValueError("Missing 'eventName' in message payload")
        
        if not event_data:
            raise ValueError("Missing 'eventData' in message payload")

        logger.info("Received event: %s", event_name)
        logger.debug("Event data: %s", event_data)

        # Get appropriate executor and process the event
        executor = executor_registry.get_executor(event_name)
        result = executor.process(event_data)
        
        logger.info("Event processed successfully. Result: %s", result)

        # delete on success
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        logger.info("Deleted message %s", message_id)
    except Exception as e:
        logger.exception("Handler failed for message %s: %s", message_id, e)
        # push to DLQ manually as fallback
        send_to_dlq(sqs_client, DLQ_URL, body, attributes={}) # type: ignore
        try:
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        except Exception:
            logger.warning("Failed to delete message after DLQ push")


def poll_loop():
    # Initialize database connection at startup
    logger.info("Initializing database connection...")
    try:
        db_client = get_mongo_client()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        raise

    # Initialize executor registry with database client
    executor_registry = ExecutorRegistry(db_client)
    logger.info("Executor registry initialized with supported events: %s", 
                executor_registry.list_supported_events())

    # Initialize SQS client
    sqs = boto3.client("sqs", region_name=AWS_REGION)
    
    logger.info("Starting listening to SQS FIFO: %s", SQS_QUEUE_URL)

    try:
        while True:
            try:
                resp = sqs.receive_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MaxNumberOfMessages=MAX_MESSAGES,
                    WaitTimeSeconds=POLL_WAIT,
                    MessageAttributeNames=["All"],
                )
            except (BotoCoreError, ClientError) as e:
                logger.error("Error receiving messages: %s", e)
                time.sleep(5)
                continue

            messages = resp.get("Messages", [])
            if not messages:
                continue

            for m in messages:
                process_message(executor_registry, m, sqs, SQS_QUEUE_URL) # pyright: ignore[reportArgumentType]

    except KeyboardInterrupt:
        logger.info("Shutting down polling loop")
    finally:
        # Close database connection on shutdown
        if db_client:
            db_client.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    poll_loop()
