"""
Sample script to send test messages to SQS FIFO queue.
This demonstrates how to send waste prediction events to the queue.
"""

import os
import json
import uuid
import boto3
from dotenv import load_dotenv
from src.constants.eventConstants import EVENT_NAMES

# Load environment variables
load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def send_waste_prediction_event(
    production_volume: float,
    rain_sum: float,
    temperature_mean: float,
    humidity_mean: float,
    wind_speed_mean: float,
    month: int,
    message_group_id: str = "waste-predictions"
):
    """
    Send a waste prediction event to SQS FIFO queue.
    
    Args:
        production_volume: Production volume in units
        rain_sum: Total rainfall in mm
        temperature_mean: Mean temperature in Celsius
        humidity_mean: Mean humidity percentage
        wind_speed_mean: Mean wind speed in km/h
        month: Month number (1-12)
        message_group_id: SQS FIFO message group ID
    """
    sqs = boto3.client("sqs", region_name=AWS_REGION)
    
    # Create the event payload
    payload = {
        "eventName": EVENT_NAMES["WASTE/PREDICTION"],
        "eventData": {
            "production_volume": production_volume,
            "rain_sum": rain_sum,
            "temperature_mean": temperature_mean,
            "humidity_mean": humidity_mean,
            "wind_speed_mean": wind_speed_mean,
            "month": month
        }
    }
    
    # Send to SQS FIFO queue
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(payload),
        MessageGroupId=message_group_id,
        MessageDeduplicationId=str(uuid.uuid4())
    )
    
    print(f"Message sent successfully!")
    print(f"Message ID: {response['MessageId']}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    return response


def send_batch_events():
    """
    Send multiple test events with different parameters.
    """
    test_scenarios = [
        {
            "production_volume": 50000,
            "rain_sum": 200,
            "temperature_mean": 28,
            "humidity_mean": 85,
            "wind_speed_mean": 15,
            "month": 6,
            "description": "High production, summer conditions"
        },
        {
            "production_volume": 30000,
            "rain_sum": 350,
            "temperature_mean": 15,
            "humidity_mean": 75,
            "wind_speed_mean": 20,
            "month": 11,
            "description": "Medium production, rainy winter"
        },
        {
            "production_volume": 75000,
            "rain_sum": 100,
            "temperature_mean": 32,
            "humidity_mean": 60,
            "wind_speed_mean": 10,
            "month": 3,
            "description": "High production, dry hot conditions"
        }
    ]
    
    print(f"Sending {len(test_scenarios)} test scenarios to SQS...")
    print("-" * 80)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario['description']}")
        description = scenario.pop('description')
        
        try:
            send_waste_prediction_event(**scenario)
        except Exception as e:
            print(f"Error sending message: {e}")
        
        print("-" * 80)


if __name__ == "__main__":
    print("Waste Prediction Event Sender")
    print("=" * 80)
    
    # Send a single test event
    print("\nSending single test event...")
    try:
        send_waste_prediction_event(
            production_volume=50000,
            rain_sum=200,
            temperature_mean=28,
            humidity_mean=85,
            wind_speed_mean=15,
            month=6
        )
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    
    # Uncomment to send batch of test scenarios
    # send_batch_events()
