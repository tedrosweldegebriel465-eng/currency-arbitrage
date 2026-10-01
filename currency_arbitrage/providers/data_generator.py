import random
import math
import csv
from typing import List, Dict, Tuple, Optional
from currency_arbitrage.config import Config

class ExchangeRateGenerator:
    """Generate realistic synthetic exchange rates"""
    
    def __init__(self):
        self.currencies: List[str] = []
        self.base_rates: Dict[str, float] = {}
        
    def generate_currencies(self) -> List[str]:
        """Generate list of major world currencies"""
        self.currencies = [
            "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL",
            "MXN", "SGD", "NZD", "HKD", "KRW", "TRY", "RUB", "ZAR", "SEK", "NOK",
            "DKK", "PLN", "THB", "IDR", "MYR"
        ]
        # Limit to Config.NUM_CURRENCIES if specified
        if hasattr(Config, 'NUM_CURRENCIES'):
            self.currencies = self.currencies[:Config.NUM_CURRENCIES]
        return self.currencies
    
    def generate_base_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """Generate realistic base exchange rates"""
        # Realistic approximate rates (as of typical market conditions)
        typical_rates = {
            "USD": 1.0, "EUR": 0.85, "GBP": 0.73, "JPY": 110.5, "CAD": 1.25,
            "AUD": 1.35, "CHF": 0.92, "CNY": 6.45, "INR": 74.5, "BRL": 5.25,
            "MXN": 20.1, "SGD": 1.35, "NZD": 1.43, "HKD": 7.78, "KRW": 1150.0,
            "TRY": 8.5, "RUB": 73.0, "ZAR": 14.5, "SEK": 8.6, "NOK": 8.4,
            "DKK": 6.3, "PLN": 3.8, "THB": 33.0, "IDR": 14500.0, "MYR": 4.2
        }
        
        # Add small random variations (+/-5%)
        self.base_rates = {}
        for curr in self.currencies:
            if curr in typical_rates:
                variation = 1 + random.uniform(-0.05, 0.05)
                self.base_rates[curr] = typical_rates[curr] * variation
            else:
                self.base_rates[curr] = random.uniform(0.5, 150.0)
        
        return self.base_rates
    
    def generate_rate(self, from_curr: str, to_curr: str) -> float:
        """Generate exchange rate between two currencies"""
        if from_curr == to_curr:
            return 1.0
        
        # Ensure base_rates exists for both currencies
        if not self.base_rates:
            self.generate_base_rates()
            
        if from_curr not in self.base_rates:
            self.base_rates[from_curr] = random.uniform(0.5, 150.0)
        if to_curr not in self.base_rates:
            self.base_rates[to_curr] = random.uniform(0.5, 150.0)
        
        # Rate = rate_to_base / rate_from_base
        try:
            rate = self.base_rates[to_curr] / self.base_rates[from_curr]
        except:
            rate = 1.0
        
        # Add small market spread (0.1-0.5%)
        spread = 1 + random.uniform(-0.005, 0.005)
        rate *= spread
        
        return rate
    
    def inject_arbitrage_cycle(self, cycle_length: int = 3) -> Tuple[List[str], List[Tuple[str, str, float]]]:
        """
        Create an artificial arbitrage opportunity
        Returns: (cycle_currencies, modified_rates)
        """
        # Select random currencies for cycle
        if len(self.currencies) < cycle_length + 1:
            cycle_length = max(2, len(self.currencies) - 1)
        
        # Pick unique currencies for the cycle
        available = [c for c in self.currencies if c in self.base_rates]
        if len(available) < cycle_length:
            cycle_length = len(available)
        
        cycle_currencies = random.sample(available, cycle_length)
        cycle_currencies.append(cycle_currencies[0])  # Complete the cycle
        
        # Calculate current product
        current_product = 1.0
        for i in range(len(cycle_currencies) - 1):
            from_c = cycle_currencies[i]
            to_c = cycle_currencies[i + 1]
            current_product *= self.generate_rate(from_c, to_c)
        
        # Boost product to >1 for profit (1% to 5% profit)
        target_product = 1.0 + random.uniform(0.01, 0.05)
        boost_factor = target_product / current_product
        
        # Modify one rate in the cycle
        modify_idx = random.randint(0, cycle_length - 2)
        from_c = cycle_currencies[modify_idx]
        to_c = cycle_currencies[modify_idx + 1]
        
        original_rate = self.generate_rate(from_c, to_c)
        new_rate = original_rate * boost_factor
        
        return cycle_currencies, [(from_c, to_c, new_rate)]
    
    def generate_complete_graph(self, inject_arbitrage: bool = True) -> Dict[Tuple[str, str], float]:
        """Generate complete exchange rate graph"""
        # Ensure currencies and base_rates are initialized
        if not self.currencies:
            self.generate_currencies()
        if not self.base_rates:
            self.generate_base_rates()
        
        rates = {}
        
        # Generate all pairs
        for from_curr in self.currencies:
            for to_curr in self.currencies:
                if from_curr != to_curr:
                    try:
                        rates[(from_curr, to_curr)] = self.generate_rate(from_curr, to_curr)
                    except:
                        # Fallback rate
                        rates[(from_curr, to_curr)] = 1.0
        
        # Inject arbitrage opportunities
        if inject_arbitrage:
            # Determine number of arbitrage cycles to inject
            num_arbitrage = max(1, int(len(self.currencies) * 0.05))  # 5% of currencies
            num_arbitrage = min(num_arbitrage, 3)  # Limit to 3 arbitrage cycles
            
            for _ in range(num_arbitrage):
                try:
                    cycle, modifications = self.inject_arbitrage_cycle()
                    for from_c, to_c, new_rate in modifications:
                        if from_c in self.currencies and to_c in self.currencies:
                            rates[(from_c, to_c)] = new_rate
                            # Also update reverse rate to maintain consistency
                            rates[(to_c, from_c)] = 1.0 / new_rate
                except Exception as e:
                    # Skip if injection fails
                    pass
        
        return rates
    
    def save_to_csv(self, rates: Dict[Tuple[str, str], float], filename: str):
        """Save rates to CSV file"""
        if not self.currencies:
            self.generate_currencies()
            
        currencies = self.currencies
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([''] + currencies)
            
            for from_curr in currencies:
                row = [from_curr]
                for to_curr in currencies:
                    if from_curr == to_curr:
                        row.append(1.0)
                    else:
                        row.append(rates.get((from_curr, to_curr), 1.0))
                writer.writerow(row)
    
    def load_from_csv(self, filename: str) -> Dict[Tuple[str, str], float]:
        """Load rates from CSV file"""
        rates = {}
        self.currencies = []
        
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # First row has currency names
            if rows:
                self.currencies = rows[0][1:]  # Skip first empty cell
                
                # Rest rows have rates
                for row in rows[1:]:
                    if row:
                        from_curr = row[0]
                        for i, to_curr in enumerate(self.currencies):
                            try:
                                rate = float(row[i + 1])
                                if rate > 0:
                                    rates[(from_curr, to_curr)] = rate
                            except:
                                pass
        
        return rates
