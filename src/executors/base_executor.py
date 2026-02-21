from abc import ABC, abstractmethod
from typing import Any, Dict
from src.utils.logger_util import logger


class BaseExecutor(ABC):
    """
    Abstract base class for all event executors.
    Each executor handles a specific event type.
    """

    def __init__(self, db_client):
        """
        Initialize executor with database client.
        
        Args:
            db_client: MongoDB client instance
        """
        self.db_client = db_client
        self.logger = logger

    @abstractmethod
    def execute(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the business logic for this event type.
        
        Args:
            event_data: Dictionary containing event payload
            
        Returns:
            Dictionary containing execution result
        """
        pass

    @abstractmethod
    def save_to_database(self, event_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Save the execution result to database.
        
        Args:
            event_data: Original event data
            result: Execution result to save
        """
        pass

    def process(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method that orchestrates execution and persistence.
        
        Args:
            event_data: Dictionary containing event payload
            
        Returns:
            Dictionary containing execution result
        """
        try:
            self.logger.info("Executing %s", self.__class__.__name__)
            
            # Execute business logic
            result = self.execute(event_data)
            
            # Save to database
            self.save_to_database(event_data, result)
            
            self.logger.info("Successfully processed event with %s", self.__class__.__name__)
            return result
            
        except Exception as e:
            self.logger.error("Error in %s: %s", self.__class__.__name__, str(e))
            raise
