# brokers/broker_base.py

from abc import ABC, abstractmethod

class BrokerBase(ABC):
    @abstractmethod
    def get_ltp(self, symbol):
        pass

    @abstractmethod
    def place_order(self, symbol, qty, order_type):
        pass

    @abstractmethod
    def get_holdings(self):
        pass

    @abstractmethod
    def get_margin(self):
        pass
