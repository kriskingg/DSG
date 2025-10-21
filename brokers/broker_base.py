# brokers/broker_base.py

from abc import ABC, abstractmethod

class BrokerBase(ABC):
    """
    Abstract base class for brokers. Each broker must implement this interface
    so that strategies can run in a broker-agnostic way.
    """

    @abstractmethod
    def get_ltp(self, symbol: str) -> float:
        """
        Get the latest traded price (LTP) of a given symbol.

        Args:
            symbol (str): The stock or instrument symbol.

        Returns:
            float: Latest traded price.
        """
        pass

    @abstractmethod
    def place_order(self, symbol: str, qty: int, order_type: str) -> dict:
        """
        Place an order for a stock or instrument.

        Args:
            symbol (str): The stock or instrument symbol.
            qty (int): Quantity to buy/sell.
            order_type (str): "buy" or "sell".

        Returns:
            dict: Order confirmation or response from the broker.
        """
        pass

    @abstractmethod
    def get_holdings(self) -> dict:
        """
        Retrieve current holdings from the broker account.

        Returns:
            dict: Dictionary of holdings with symbol as key.
        """
        pass

    @abstractmethod
    def get_margin(self) -> dict:
        """
        Retrieve margin and cash availability from broker.

        Returns:
            dict: Dictionary with margin information like available cash, used margin, etc.
        """
        pass
