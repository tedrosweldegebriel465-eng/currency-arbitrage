# Configuration settings
class Config:
    # Algorithm parameters
    NUM_CURRENCIES = 25
    MAX_ITERATIONS = 100
    
    # Arbitrage detection
    PROFIT_THRESHOLD = 0.0001  # 0.01% minimum profit
    
    # Data generation
    MIN_RATE = 0.0001
    MAX_RATE = 10000
    ARBITRAGE_PROBABILITY = 0.05  # 5% chance to create arbitrage
    
    # Logging
    LOG_LEVEL = "INFO"
    SHOW_DETAILED_PATHS = True
    
    # File paths
    DATA_PATH = "data/inputs/exchange_rates.csv"
    OUTPUT_PATH = "output/reports/text/arbitrage_results.txt"