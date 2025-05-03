import logging
from enum import IntEnum

# Custom log level for money transactions
class CustomLogLevels(IntEnum):
    TRANSACTION = 25  # Between INFO (20) and WARNING (30)

# Register the new log level
logging.addLevelName(CustomLogLevels.TRANSACTION, "TRANSACTION")

def get_transaction_logger():
    """Returns a logger configured for money transactions"""
    # Create a transaction logger
    transaction_logger = logging.getLogger("transaction")
    
    # Add a method for the TRANSACTION level
    def transaction(self, message, *args, **kwargs):
        if self.isEnabledFor(CustomLogLevels.TRANSACTION):
            self._log(CustomLogLevels.TRANSACTION, message, args, **kwargs)
    
    # Add the method to the logger class
    logging.Logger.transaction = transaction
    
    return transaction_logger

def setup_logging():
    """Configure logging for the application"""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    # Configure transaction logger with file handler
    transaction_handler = logging.FileHandler("transactions.log")
    transaction_handler.setLevel(CustomLogLevels.TRANSACTION)
    transaction_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    transaction_logger = get_transaction_logger()
    transaction_logger.setLevel(CustomLogLevels.TRANSACTION)
    transaction_logger.addHandler(transaction_handler)