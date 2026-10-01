"""
Live Exchange Rate API Integration
Fetches real-time forex rates from free APIs
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import requests


class LiveExchangeRateAPI:
    """Fetch live exchange rates from free APIs."""

    def __init__(self, api_source: str = "exchangerate-api"):
        """
        Initialize API client.
        Sources: 'exchangerate-api', 'frankfurter', 'currencyapi'
        """
        self.api_source = api_source
        self.cache = {}
        self.cache_duration = 60
        self.currencies = []
        self.api_urls = {
            "exchangerate-api": "https://api.exchangerate-api.com/v4/latest/",
            "frankfurter": "https://api.frankfurter.app/latest",
            "currencyapi": "https://api.currencyapi.com/v3/latest",
        }

    def fetch_live_rates(self, base_currency: str = "USD") -> Optional[Dict]:
        """
        Fetch live exchange rates from API.
        Returns: Dictionary of currency -> rate
        """
        cache_key = f"{base_currency}_{int(time.time() / self.cache_duration)}"
        if cache_key in self.cache:
            print("   Using cached rates (updated within last minute)")
            return self.cache[cache_key]

        try:
            if self.api_source == "exchangerate-api":
                url = f"{self.api_urls['exchangerate-api']}{base_currency}"
                response = requests.get(url, timeout=10)
                data = response.json()

                if "rates" in data:
                    rates = data["rates"]
                    self.cache[cache_key] = rates
                    print(f"   [OK] Fetched live rates from {self.api_source}")
                    print(f"   [OK] Base: {base_currency}, {len(rates)} currencies")
                    return rates

            elif self.api_source == "frankfurter":
                url = f"{self.api_urls['frankfurter']}?from={base_currency}"
                response = requests.get(url, timeout=10)
                data = response.json()

                if "rates" in data:
                    rates = data["rates"]
                    self.cache[cache_key] = rates
                    print(f"   [OK] Fetched live rates from {self.api_source}")
                    return rates

        except requests.exceptions.RequestException as e:
            print(f"   [WARNING] API Error: {e}")
            print("   Falling back to generated data...")
            return None
        except Exception as e:
            print(f"   [WARNING] Error: {e}")
            return None

        return None

    def update_graph_with_live_rates(self, graph, base_currency: str = "USD"):
        """Update existing graph with live exchange rates."""
        live_rates = self.fetch_live_rates(base_currency)

        if not live_rates:
            print("   [ERROR] Failed to fetch live rates")
            return False

        graph.edges.clear()
        graph.rates.clear()

        for to_currency, rate in live_rates.items():
            if to_currency in graph.currency_to_idx:
                graph.add_rate(base_currency, to_currency, rate)
                if rate > 0:
                    graph.add_rate(to_currency, base_currency, 1.0 / rate)

        currencies = list(graph.currencies)
        for i, from_curr in enumerate(currencies):
            for j, to_curr in enumerate(currencies):
                if i != j and from_curr != base_currency and to_curr != base_currency:
                    if from_curr in live_rates and to_curr in live_rates:
                        rate = live_rates[to_curr] / live_rates[from_curr]
                        graph.add_rate(from_curr, to_curr, rate)

        print(f"   [OK] Graph updated with {len(live_rates)} live exchange rates")
        return True


class SimulatedLiveRates:
    """Simulate live rate changes for testing."""

    def __init__(self, base_generator):
        self.generator = base_generator
        self.last_update = datetime.now()

    def get_simulated_live_rates(self, volatility: float = 0.001) -> Dict:
        """
        Simulate live rate changes with small random fluctuations.
        volatility: 0.001 = 0.1% random change
        """
        rates = self.generator.generate_complete_graph(inject_arbitrage=False)

        for pair in rates:
            change = 1 + (volatility * (2 * (hash(str(pair)) % 1000) / 1000 - 1))
            rates[pair] *= change

        return rates


class MultiProviderRateComparator:
    """Compare rates from multiple providers and surface mismatches."""

    def __init__(self):
        self.supported_providers = ["exchangerate-api", "frankfurter"]

    def fetch_from_providers(self, base_currency: str = "USD", providers=None) -> Dict[str, Dict[str, float]]:
        providers = providers or self.supported_providers
        results = {}

        for provider in providers:
            api = LiveExchangeRateAPI(api_source=provider)
            rates = api.fetch_live_rates(base_currency)
            if rates:
                results[provider] = rates

        return results

    def compare_provider_rates(self, base_currency: str = "USD", providers=None) -> Dict:
        provider_rates = self.fetch_from_providers(base_currency=base_currency, providers=providers)
        mismatches = []
        all_currencies = set()

        for rates in provider_rates.values():
            all_currencies.update(rates.keys())

        for currency in sorted(all_currencies):
            samples = []
            for provider, rates in provider_rates.items():
                if currency in rates and rates[currency] > 0:
                    samples.append((provider, rates[currency]))

            if len(samples) < 2:
                continue

            lowest_provider, lowest_rate = min(samples, key=lambda item: item[1])
            highest_provider, highest_rate = max(samples, key=lambda item: item[1])
            spread_percent = ((highest_rate - lowest_rate) / lowest_rate) * 100 if lowest_rate else 0.0

            mismatches.append(
                {
                    "currency": currency,
                    "lowest_provider": lowest_provider,
                    "highest_provider": highest_provider,
                    "lowest_rate": lowest_rate,
                    "highest_rate": highest_rate,
                    "spread_percent": spread_percent,
                }
            )

        mismatches.sort(key=lambda item: item["spread_percent"], reverse=True)
        return {
            "base_currency": base_currency,
            "provider_rates": provider_rates,
            "mismatches": mismatches,
        }
