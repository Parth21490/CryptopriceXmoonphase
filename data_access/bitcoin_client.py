"""
Cryptocurrency Data Client for Bybit API integration.
Handles fetching crypto data (BTC, ETH, SOL) with proper error handling and rate limiting.
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CryptoPriceData:
    """Data model for cryptocurrency price information."""
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    symbol: str  # Added symbol field
    
    def price_change_percentage(self, previous_price: float) -> float:
        """Calculate day-over-day price change percentage."""
        if previous_price == 0:
            return 0.0
        return ((self.close_price - previous_price) / previous_price) * 100


# Keep backward compatibility
BitcoinPriceData = CryptoPriceData


class CryptoDataClient:
    """Client for fetching cryptocurrency data from Bybit V5 Public API."""
    
    BASE_URL = "https://api.bybit.com"
    RATE_LIMIT_DELAY = 0.1  # 100ms between requests
    
    # Supported cryptocurrencies
    SUPPORTED_CRYPTOS = {
        'Bitcoin': 'BTCUSDT',
        'Ethereum': 'ETHUSDT', 
        'Solana': 'SOLUSDT'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoMoonDashboard/1.0'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a rate-limited request to the Bybit API."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API-level errors
            if data.get('retCode') != 0:
                error_msg = data.get('retMsg', 'Unknown API error')
                raise requests.RequestException(f"API Error: {error_msg}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout when fetching Bitcoin data")
            raise
        except requests.exceptions.ConnectionError:
            logger.error("Connection error when fetching Bitcoin data")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error when fetching Bitcoin data: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when fetching Bitcoin data: {e}")
            raise
    
    def fetch_crypto_data(self, crypto_name: str = 'Bitcoin', limit: int = 1000) -> List[CryptoPriceData]:
        """
        Fetch cryptocurrency daily data from Bybit V5 Public API.
        
        Args:
            crypto_name: Name of cryptocurrency ('Bitcoin', 'Ethereum', 'Solana')
            limit: Number of data points to fetch (max 1000)
            
        Returns:
            List of CryptoPriceData objects
            
        Raises:
            requests.RequestException: If API request fails
            ValueError: If data validation fails or unsupported crypto
        """
        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        
        if crypto_name not in self.SUPPORTED_CRYPTOS:
            raise ValueError(f"Unsupported cryptocurrency: {crypto_name}. Supported: {list(self.SUPPORTED_CRYPTOS.keys())}")
        
        symbol = self.SUPPORTED_CRYPTOS[crypto_name]
        
        endpoint = "/v5/market/kline"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': 'D',
            'limit': limit
        }
        
        logger.info(f"Fetching {limit} days of {symbol} data from Bybit")
        
        try:
            data = self._make_request(endpoint, params)
            
            # Extract kline data
            klines = data.get('result', {}).get('list', [])
            
            if not klines:
                logger.warning(f"No kline data received from API for {symbol}")
                return []
            
            # Parse and validate data
            crypto_data = []
            for kline in klines:
                try:
                    parsed_data = self._parse_kline_data(kline, symbol)
                    if self._validate_price_data(parsed_data, crypto_name):
                        crypto_data.append(parsed_data)
                    else:
                        logger.warning(f"Invalid data point skipped: {kline}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse kline data: {kline}, error: {e}")
                    continue
            
            # Sort by date (oldest first)
            crypto_data.sort(key=lambda x: x.date)
            
            logger.info(f"Successfully fetched and parsed {len(crypto_data)} data points for {symbol}")
            return crypto_data
            
        except Exception as e:
            logger.error(f"Failed to fetch {crypto_name} data: {e}")
            raise
    
    def fetch_btcusdt_data(self, limit: int = 1000) -> List[CryptoPriceData]:
        """
        Backward compatibility method for fetching Bitcoin data.
        
        Args:
            limit: Number of data points to fetch (max 1000)
            
        Returns:
            List of CryptoPriceData objects
        """
        return self.fetch_crypto_data('Bitcoin', limit)
    
    def _parse_kline_data(self, kline: List[str], symbol: str = 'BTCUSDT') -> CryptoPriceData:
        """
        Parse raw kline data from Bybit API response.
        
        Bybit kline format: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
        """
        if len(kline) < 6:
            raise ValueError(f"Invalid kline data format: {kline}")
        
        try:
            # Convert timestamp from milliseconds to datetime
            timestamp_ms = int(kline[0])
            date = datetime.fromtimestamp(timestamp_ms / 1000)
            
            # Parse price data
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            volume = float(kline[5])
            
            return CryptoPriceData(
                date=date,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                symbol=symbol
            )
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse numeric values from kline: {kline}") from e
    
    def _validate_price_data(self, data: CryptoPriceData, crypto_name: str = 'Bitcoin') -> bool:
        """
        Validate that price data contains all required fields and reasonable values.
        
        Args:
            data: CryptoPriceData object to validate
            crypto_name: Name of cryptocurrency for validation ranges
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check that all required fields are present and not None
            if data.date is None or data.symbol is None:
                return False
            
            # Check that all prices are positive numbers
            prices = [data.open_price, data.high_price, data.low_price, data.close_price]
            if any(price <= 0 for price in prices):
                return False
            
            # Check that volume is non-negative
            if data.volume < 0:
                return False
            
            # Check price relationships (high >= low, etc.)
            if data.high_price < data.low_price:
                return False
            
            if not (data.low_price <= data.open_price <= data.high_price):
                return False
            
            if not (data.low_price <= data.close_price <= data.high_price):
                return False
            
            # Check for reasonable price ranges based on cryptocurrency
            price_ranges = {
                'Bitcoin': (1, 1_000_000),      # $1 to $1M
                'Ethereum': (0.1, 100_000),     # $0.1 to $100K  
                'Solana': (0.01, 10_000)        # $0.01 to $10K
            }
            
            min_price, max_price = price_ranges.get(crypto_name, (0.001, 1_000_000))
            if any(price < min_price or price > max_price for price in prices):
                return False
            
            return True
            
        except (AttributeError, TypeError):
            return False
    
    def normalize_data(self, data_list: List[CryptoPriceData]) -> List[CryptoPriceData]:
        """
        Normalize and clean the data list.
        
        Args:
            data_list: List of CryptoPriceData objects
            
        Returns:
            Normalized and cleaned list
        """
        if not data_list:
            return []
        
        # Remove duplicates based on date
        seen_dates = set()
        normalized_data = []
        
        for data in data_list:
            date_key = data.date.date()  # Use date only, ignore time
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                normalized_data.append(data)
        
        # Sort by date
        normalized_data.sort(key=lambda x: x.date)
        
        logger.info(f"Normalized data: {len(data_list)} -> {len(normalized_data)} points")
        return normalized_data


# Keep backward compatibility
BitcoinDataClient = CryptoDataClient