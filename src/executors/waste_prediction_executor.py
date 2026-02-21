from typing import Any, Dict
from datetime import datetime
from waste_predictor import predict_waste

from constants.eventConstants import EVENT_NAMES
from .base_executor import BaseExecutor


class WastePredictionExecutor(BaseExecutor):
    """
    Executor for waste prediction events.
    Processes waste prediction requests and stores results in MongoDB.
    """

    def __init__(self, db_client):
        super().__init__(db_client)
        self.db = db_client.get_database("waste_management")
        self.collection = self.db.get_collection("waste_predictions")

    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute waste prediction using the waste-predictor library.
        
        Args:
            event_data: Dictionary containing prediction parameters:
                - production_volume: Production volume in units
                - rain_sum: Total rainfall in mm
                - temperature_mean: Mean temperature in Celsius
                - humidity_mean: Mean humidity percentage
                - wind_speed_mean: Mean wind speed in km/h
                - month: Month number (1-12)
                
        Returns:
            Dictionary containing prediction results
        """
        # Extract parameters
        production_volume = event_data.get("production_volume")
        rain_sum = event_data.get("rain_sum")
        temperature_mean = event_data.get("temperature_mean")
        humidity_mean = event_data.get("humidity_mean")
        wind_speed_mean = event_data.get("wind_speed_mean")
        month = event_data.get("month")
        metadata = event_data.get("metadata", {})
        request_id = metadata.get("request_id", "unknown")

        # Validate required parameters
        required_params = {
            "production_volume": production_volume,
            "rain_sum": rain_sum,
            "temperature_mean": temperature_mean,
            "humidity_mean": humidity_mean,
            "wind_speed_mean": wind_speed_mean,
            "month": month,
            "metadata": metadata
        }
        
        metadata_required = ["request_id"]
        missing_metadata = [k for k in metadata_required if k not in metadata or metadata[k] is None]
        if missing_metadata:
            raise ValueError(f"Missing required metadata fields: {', '.join(missing_metadata)}")

        missing_params = [k for k, v in required_params.items() if v is None]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        self.logger.info(
            "Predicting waste for production_volume=%s, month=%s, request_id=%s",
            production_volume,
            month,
            request_id
        )

        # Call waste prediction library
        # Type assertions safe after validation
        result = predict_waste(
            production_volume=float(production_volume),  # type: ignore
            rain_sum=float(rain_sum),  # type: ignore
            temperature_mean=float(temperature_mean),  # type: ignore
            humidity_mean=float(humidity_mean),  # type: ignore
            wind_speed_mean=float(wind_speed_mean),  # type: ignore
            month=int(month)  # type: ignore
        )

        total_waste = result.get("Total_Waste_kg", 0)
        self.logger.info("Prediction result: Total Waste = %.2f kg", total_waste)

        return result

    def save_to_database(self, event_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Save waste prediction result to MongoDB.
        
        Args:
            event_data: Original event data with input parameters and request metadata
            result: Prediction result from waste predictor
        """
        metadata = event_data.get("metadata", {})
        request_id = metadata.get("request_id", "unknown")
        
        document = {
            "timestamp": datetime.utcnow(),
            "input_parameters": {
                "production_volume": event_data.get("production_volume"),
                "rain_sum": event_data.get("rain_sum"),
                "temperature_mean": event_data.get("temperature_mean"),
                "humidity_mean": event_data.get("humidity_mean"),
                "wind_speed_mean": event_data.get("wind_speed_mean"),
                "month": event_data.get("month")
            },
            "prediction_result": result,
            "metadata": {
                "event_type": EVENT_NAMES["WASTE/PREDICTION"],
                "processor_version": "1.0.0",
                "request_id": request_id
            }
        }

        # Insert into MongoDB
        insert_result = self.collection.insert_one(document)
        self.logger.info(
            "Saved prediction to database with ID: %s",
            insert_result.inserted_id
        )
