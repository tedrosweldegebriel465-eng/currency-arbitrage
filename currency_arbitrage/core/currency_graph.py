import math
import csv
from typing import List, Tuple, Dict, Optional

class CurrencyGraph:
    """Represents the currency exchange graph"""
    
    def __init__(self):
        self.currencies: List[str] = []
        self.currency_to_idx: Dict[str, int] = {}
        self.edges: List[Tuple[int, int, float]] = []
        self.rates: Dict[Tuple[int, int], float] = {}
        
    def add_currency(self, name: str) -> int:
        """Add a currency and return its index"""
        if name not in self.currency_to_idx:
            self.currency_to_idx[name] = len(self.currencies)
            self.currencies.append(name)
        return self.currency_to_idx[name]
    
    def add_rate(self, from_curr: str, to_curr: str, rate: float):
        """Add exchange rate from one currency to another"""
        from_idx = self.add_currency(from_curr)
        to_idx = self.add_currency(to_curr)
        
        # Store actual rate
        self.rates[(from_idx, to_idx)] = rate
        
        # Convert to log weight for Bellman-Ford
        weight = -math.log(rate)
        self.edges.append((from_idx, to_idx, weight))
    
    def add_bidirectional_rates(self, curr1: str, curr2: str, rate1_to_2: float):
        """Add rates in both directions"""
        self.add_rate(curr1, curr2, rate1_to_2)
        self.add_rate(curr2, curr1, 1.0 / rate1_to_2)
    
    def get_rate(self, from_idx: int, to_idx: int) -> Optional[float]:
        """Get exchange rate between two currencies"""
        return self.rates.get((from_idx, to_idx))
    
    def get_currency_name(self, idx: int) -> str:
        """Get currency name by index"""
        return self.currencies[idx]
    
    def get_num_currencies(self) -> int:
        return len(self.currencies)
    
    def get_num_edges(self) -> int:
        return len(self.edges)
    
    def load_from_csv(self, filename: str):
        """Load exchange rates from CSV file"""
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # First row: currency names
            currencies = headers[1:]
            
            for curr in currencies:
                self.add_currency(curr)
            
            for row in reader:
                from_curr = row[0]
                rates = row[1:]
                for to_curr, rate in zip(currencies, rates):
                    if rate and float(rate) > 0:
                        self.add_rate(from_curr, to_curr, float(rate))
    
    def __str__(self) -> str:
        return f"CurrencyGraph({len(self.currencies)} currencies, {len(self.edges)} edges)"