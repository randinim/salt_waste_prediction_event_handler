from typing import Dict, Type
from .base_executor import BaseExecutor
from .waste_prediction_executor import WastePredictionExecutor
from src.utils.logger_util import logger
from src.constants.eventConstants import EVENT_NAMES


class ExecutorRegistry:
    """
    Registry for mapping event names to their corresponding executor classes.
    This uses a factory pattern to instantiate the appropriate executor based on event type.
    """

    def __init__(self, db_client):
        """
        Initialize the executor registry with database client.
        
        Args:
            db_client: MongoDB client instance to pass to executors
        """
        self.db_client = db_client
        self.logger = logger
        
        # Map event names to executor classes
        self._executor_map: Dict[str, Type[BaseExecutor]] = {
            EVENT_NAMES["WASTE/PREDICTION"]: WastePredictionExecutor,
            # Add more event types here as needed
            # "OtherEvent": OtherExecutor,
        }

    def get_executor(self, event_name: str) -> BaseExecutor:
        """
        Get an executor instance for the given event name.
        
        Args:
            event_name: The name of the event to process
            
        Returns:
            An instance of the appropriate executor
            
        Raises:
            ValueError: If no executor is registered for the event name
        """
        executor_class = self._executor_map.get(event_name)
        
        if not executor_class:
            available_events = ", ".join(self._executor_map.keys())
            error_msg = (
                f"No executor found for event '{event_name}'. "
                f"Available events: {available_events}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug("Creating executor %s for event %s", executor_class.__name__, event_name)
        return executor_class(self.db_client)

    def register_executor(self, event_name: str, executor_class: Type[BaseExecutor]) -> None:
        """
        Register a new executor for an event type.
        Allows dynamic registration of executors at runtime.
        
        Args:
            event_name: The name of the event
            executor_class: The executor class to handle this event
        """
        self.logger.info("Registering executor %s for event %s", executor_class.__name__, event_name)
        self._executor_map[event_name] = executor_class

    def list_supported_events(self) -> list:
        """
        Get a list of all supported event names.
        
        Returns:
            List of supported event names
        """
        return list(self._executor_map.keys())
