#!/usr/bin/env python3
"""
� Crypto Moon Dashboard
A comprehensive cryptocurrency analysis tool that correlates price movements with lunar phases.

Features:
- Multi-cryptocurrency support (Bitcoin, Ethereum, Solana)
- Real-time data from CoinGecko API
- Lunar phase calculations and correlations
- Interactive dark-themed dashboard
- Statistical analysis and visualizations

Author: AI Assistant
License: MIT
"""

import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Handle optional imports with error messages
try:
    import plotly.graph_objects as go
except ImportError:
    st.error("� Plotly is not installed. Please install it with: pip install plotly>=5.15.0")
    st.stop()

try:
    import ephem
except ImportError:
    st.error("� PyEphem is not installed. Please install it with: pip install pyephem>=4.1.4")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CryptoPriceData:
    """Data model for cryptocurrency price information."""
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    symbol: str
    
    def price_change_percentage(self, previous_price: float) -> float:
        """Calculate day-over-day price change percentage."""
        if previous_price == 0:
            return 0.0
        return ((self.close_price - previous_price) / previous_price) * 100

@dataclass
class MoonPhaseData:
    """Data model for moon phase information."""
    date: datetime
    phase_percentage: float  # 0-100%
    
    @property
    def is_full_moon(self) -> bool:
        return self.phase_percentage > 98.0

@dataclass
class CombinedDataPoint:
    """Combined data point containing cryptocurrency price and moon phase data."""
    date: datetime
    crypto_data: CryptoPriceData
    moon_data: MoonPhaseData
    price_change: Optional[float] = None
@dataclass
class AnalysisResults:
    """Results from correlation analysis."""
    full_moon_avg_change: float
    normal_day_avg_change: float
    full_moon_count: int
    normal_day_count: int
    total_data_points: int
    
    @property
    def difference(self) -> float:
        return self.full_moon_avg_change - self.normal_day_avg_change
    
    @property
    def full_moon_percentage(self) -> float:
        if self.total_data_points == 0:
            return 0.0
        return (self.full_moon_count / self.total_data_points) * 100
    
    @property
    def has_sufficient_data(self) -> bool:
        return self.full_moon_count >= 1 and self.normal_day_count >= 1

# ============================================================================
# CRYPTOCURRENCY DATA CLIENT
# ============================================================================

class CryptoDataClient:
    """Client for fetching cryptocurrency data from CoinGecko API."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    RATE_LIMIT_DELAY = 1.0  # 1 second between requests to be respectful
    
    # Supported cryptocurrencies with CoinGecko IDs
    SUPPORTED_CRYPTOS = {
        'Bitcoin': 'bitcoin',
        'Ethereum': 'ethereum',
        'Solana': 'solana'
    }
    
    # Symbol mapping for display
    CRYPTO_SYMBOLS = {
        'Bitcoin': 'BTCUSDT',
        'Ethereum': 'ETHUSDT', 
        'Solana': 'SOLUSDT'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoMoonDashboard/1.0 (Educational Project)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = time.time()
    

    def fetch_crypto_data(self, crypto_name: str = 'Bitcoin', limit: int = 1000) -> List[CryptoPriceData]:
        """Fetch cryptocurrency daily data from CoinGecko API with demo fallback."""
        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        
        if crypto_name not in self.SUPPORTED_CRYPTOS:
            raise ValueError(f"Unsupported cryptocurrency: {crypto_name}. Supported: {list(self.SUPPORTED_CRYPTOS.keys())}")
        
        # Try CoinGecko API first, then demo data as fallback
        data_sources = [
            ("CoinGecko API", self._fetch_from_coingecko),
            ("Demo Data", self._generate_demo_data)
        ]
        
        for source_name, fetch_method in data_sources:
            try:
                logger.info(f"Trying {source_name} for {crypto_name}...")
                data = fetch_method(crypto_name, limit)
                if data and len(data) > 0:
                    logger.info(f"✅ Successfully fetched {len(data)} data points from {source_name}")
                    return data
                else:
                    logger.warning(f"❌ {source_name} returned no data")
            except Exception as e:
                logger.warning(f"❌ {source_name} failed: {str(e)[:100]}...")
                continue
        
        # If we get here, all sources failed - return minimal demo data
        logger.error("🚨 All data sources failed! Generating minimal demo data...")
        return self._generate_minimal_demo_data(crypto_name, limit)
    
    def _fetch_from_coingecko(self, crypto_name: str, limit: int) -> List[CryptoPriceData]:
        """Primary method to fetch data from CoinGecko API."""
        if crypto_name not in self.SUPPORTED_CRYPTOS:
            raise ValueError(f"CoinGecko not available for {crypto_name}")
        
        coin_id = self.SUPPORTED_CRYPTOS[crypto_name]
        symbol = self.CRYPTO_SYMBOLS[crypto_name]
        
        # CoinGecko free API endpoint for historical data
        endpoint = f"/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': min(limit, 365),  # CoinGecko free tier limit
            'interval': 'daily'
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            prices = data.get('prices', [])
            
            if not prices:
                raise ValueError("No price data received from CoinGecko")
            
            crypto_data = []
            for price_point in prices[-limit:]:  # Get the most recent data points
                timestamp_ms = price_point[0]
                price = price_point[1]
                
                date = datetime.fromtimestamp(timestamp_ms / 1000)
                
                # CoinGecko only provides close price, so we'll use it for all OHLC values
                crypto_data.append(CryptoPriceData(
                    date=date,
                    open_price=price * 0.999,  # Approximate open price
                    high_price=price * 1.001,  # Approximate high price
                    low_price=price * 0.999,   # Approximate low price
                    close_price=price,
                    volume=1000000.0,  # Default volume since CoinGecko free tier doesn't provide it
                    symbol=symbol
                ))
            
            logger.info(f"Successfully fetched {len(crypto_data)} data points from CoinGecko for {crypto_name}")
            return crypto_data
            
        except Exception as e:
            logger.error(f"CoinGecko fallback failed: {e}")
            raise
    

    
    def _generate_demo_data(self, crypto_name: str, limit: int) -> List[CryptoPriceData]:
        """Generate demo cryptocurrency data when APIs are unavailable."""
        try:
            import random
            
            logger.info(f"Generating demo data for {crypto_name} with {limit} data points")
            
            # Base prices for different cryptocurrencies
            base_prices = {
                'Bitcoin': 45000.0,
                'Ethereum': 3000.0,
                'Solana': 100.0
            }
            
            base_price = base_prices.get(crypto_name, 1000.0)
            symbol = self.SUPPORTED_CRYPTOS[crypto_name]
            
            crypto_data = []
            current_price = base_price
            
            # Generate data for the last 'limit' days
            for i in range(limit):
                # Create date going backwards from today
                date = datetime.now() - pd.Timedelta(days=limit - i - 1)
                
                # Generate realistic price movements (±5% daily change)
                daily_change = random.uniform(-0.05, 0.05)
                current_price *= (1 + daily_change)
                
                # Generate OHLC data around the current price
                open_price = current_price * random.uniform(0.995, 1.005)
                high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
                low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
                close_price = current_price
                volume = random.uniform(500000, 2000000)
                
                crypto_data.append(CryptoPriceData(
                    date=date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume,
                    symbol=symbol
                ))
            
            logger.info(f"Generated {len(crypto_data)} demo data points for {crypto_name}")
            return crypto_data
        
        except Exception as e:
            logger.error(f"Demo data generation failed: {e}")
            # Return minimal fallback data
            return self._generate_minimal_demo_data(crypto_name, limit)
    
    def _generate_minimal_demo_data(self, crypto_name: str, limit: int) -> List[CryptoPriceData]:
        """Generate minimal demo data as absolute last resort."""
        logger.info(f"🚨 Generating minimal demo data for {crypto_name} (last resort)")
        
        # Simple base prices
        base_prices = {'Bitcoin': 45000.0, 'Ethereum': 3000.0, 'Solana': 100.0}
        base_price = base_prices.get(crypto_name, 1000.0)
        symbol = self.SUPPORTED_CRYPTOS[crypto_name]
        
        crypto_data = []
        for i in range(min(limit, 30)):  # Limit to 30 days for minimal data
            date = datetime.now() - pd.Timedelta(days=30 - i - 1)
            price = base_price * (1 + (i % 10 - 5) * 0.01)  # Simple price variation
            
            crypto_data.append(CryptoPriceData(
                date=date,
                open_price=price * 0.999,
                high_price=price * 1.001,
                low_price=price * 0.998,
                close_price=price,
                volume=1000000.0,
                symbol=symbol
            ))
        
        logger.info(f"Generated {len(crypto_data)} minimal demo data points")
        return crypto_data
    
    def _validate_price_data(self, data: CryptoPriceData, crypto_name: str = 'Bitcoin') -> bool:
        """Validate that price data contains all required fields and reasonable values."""
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

# ============================================================================
# MOON PHASE CALCULATOR
# ============================================================================

class MoonPhaseCalculator:
    """Calculator for moon phases using astronomical computations."""
    
    def __init__(self):
        """Initialize the moon phase calculator."""
        pass
    
    def calculate_moon_phase(self, target_date: datetime) -> MoonPhaseData:
        """Calculate moon phase for a specific date."""
        try:
            # Create observer (location doesn't matter for moon phase)
            observer = ephem.Observer()
            observer.date = target_date.strftime('%Y/%m/%d')
            
            # Create moon object
            moon = ephem.Moon()
            moon.compute(observer)
            
            # Calculate phase percentage (0-100%)
            phase_percentage = moon.moon_phase * 100
            
            return MoonPhaseData(
                date=target_date,
                phase_percentage=phase_percentage
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate moon phase for {target_date}: {e}")
            raise
    
    def calculate_moon_phases_for_dates(self, dates: List[datetime]) -> List[MoonPhaseData]:
        """Calculate moon phases for multiple dates."""
        if not dates:
            logger.warning("No dates provided for moon phase calculation")
            return []
        
        moon_phases = []
        for date in dates:
            try:
                moon_phase = self.calculate_moon_phase(date)
                moon_phases.append(moon_phase)
            except Exception as e:
                logger.warning(f"Failed to calculate moon phase for {date}: {e}")
                continue
        
        logger.info(f"Successfully calculated moon phases for {len(moon_phases)} dates")
        return moon_phases
# ============================================================================
# DATA PROCESSOR
# ============================================================================

class DataProcessor:
    """Processor for combining cryptocurrency price data with moon phase calculations."""
    
    def __init__(self):
        """Initialize the data processor."""
        self._combined_data: List[CombinedDataPoint] = []
        self._data_cache: Dict[date, CombinedDataPoint] = {}
    
    def combine_data(self, crypto_data: List[CryptoPriceData], 
                    moon_data: List[MoonPhaseData]) -> List[CombinedDataPoint]:
        """Combine cryptocurrency price data with moon phase data maintaining date-based relationships."""
        if not crypto_data:
            logger.warning("No cryptocurrency data provided for combination")
            return []
        
        if not moon_data:
            logger.warning("No moon phase data provided for combination")
            return []
        
        # Create lookup dictionary for moon data by date
        moon_lookup = {}
        for moon_point in moon_data:
            if moon_point and moon_point.date:
                date_key = moon_point.date.date()
                moon_lookup[date_key] = moon_point
        
        # Combine data points with matching dates
        combined_points = []
        matched_count = 0
        
        for crypto_point in crypto_data:
            if not crypto_point or not crypto_point.date:
                logger.warning("Skipping invalid cryptocurrency data point")
                continue
            
            date_key = crypto_point.date.date()
            
            if date_key in moon_lookup:
                moon_point = moon_lookup[date_key]
                
                combined_point = CombinedDataPoint(
                    date=crypto_point.date,
                    crypto_data=crypto_point,
                    moon_data=moon_point
                )
                
                combined_points.append(combined_point)
                matched_count += 1
            else:
                logger.debug(f"No moon data found for cryptocurrency date: {date_key}")
        
        # Sort by date
        combined_points.sort(key=lambda x: x.date)
        
        logger.info(f"Combined {matched_count} data points from {len(crypto_data)} cryptocurrency "
                   f"and {len(moon_data)} moon phase data points")
        
        # Store in cache and instance variable
        self._combined_data = combined_points
        self._update_cache(combined_points)
        
        return combined_points
    
    def calculate_price_changes(self, combined_data: Optional[List[CombinedDataPoint]] = None) -> List[CombinedDataPoint]:
        """Calculate day-over-day price changes using the formula: ((current_price - previous_price) / previous_price) * 100"""
        data_to_process = combined_data if combined_data is not None else self._combined_data
        
        if not data_to_process:
            logger.warning("No data available for price change calculation")
            return []
        
        # Sort data by date to ensure proper order
        sorted_data = sorted(data_to_process, key=lambda x: x.date)
        
        previous_price = None
        
        for i, data_point in enumerate(sorted_data):
            if not data_point.crypto_data:
                logger.warning(f"Skipping data point with missing cryptocurrency data: {data_point.date}")
                continue
            
            current_price = data_point.crypto_data.close_price
            
            if previous_price is not None and previous_price != 0:
                price_change = ((current_price - previous_price) / previous_price) * 100
                data_point.price_change = price_change
            else:
                # First data point has no previous price for comparison
                data_point.price_change = None
            
            previous_price = current_price
        
        logger.info(f"Calculated price changes for {len(sorted_data)} data points")
        return sorted_data
    
    def _update_cache(self, combined_data: List[CombinedDataPoint]) -> None:
        """Update the internal cache with combined data points."""
        self._data_cache.clear()
        for data_point in combined_data:
            if data_point and data_point.date:
                date_key = data_point.date.date()
                self._data_cache[date_key] = data_point
# ============================================================================
# CORRELATION ANALYZER
# ============================================================================

class CorrelationAnalyzer:
    """Analyzer for statistical correlation between cryptocurrency prices and moon phases."""
    
    def __init__(self, full_moon_threshold: float = 98.0, min_data_points: int = 1):
        """Initialize the correlation analyzer."""
        self.full_moon_threshold = full_moon_threshold
        self.min_data_points = min_data_points
    
    def analyze_correlation(self, combined_data: List[CombinedDataPoint]) -> AnalysisResults:
        """Perform correlation analysis between cryptocurrency prices and moon phases."""
        if not combined_data:
            logger.warning("No data provided for correlation analysis")
            return AnalysisResults(0.0, 0.0, 0, 0, 0)
        
        # Filter data points with valid price changes
        valid_data = [point for point in combined_data if point.price_change is not None]
        
        if not valid_data:
            logger.warning("No valid price change data for correlation analysis")
            return AnalysisResults(0.0, 0.0, 0, 0, 0)
        
        # Separate full moon and normal day data
        full_moon_changes = []
        normal_day_changes = []
        
        for point in valid_data:
            if point.moon_data.is_full_moon:
                full_moon_changes.append(point.price_change)
            else:
                normal_day_changes.append(point.price_change)
        
        # Calculate averages
        full_moon_avg = sum(full_moon_changes) / len(full_moon_changes) if full_moon_changes else 0.0
        normal_day_avg = sum(normal_day_changes) / len(normal_day_changes) if normal_day_changes else 0.0
        
        results = AnalysisResults(
            full_moon_avg_change=full_moon_avg,
            normal_day_avg_change=normal_day_avg,
            full_moon_count=len(full_moon_changes),
            normal_day_count=len(normal_day_changes),
            total_data_points=len(valid_data)
        )
        
        logger.info(f"Correlation analysis complete: {results.full_moon_count} full moon days, {results.normal_day_count} normal days")
        
        return results
    
    def handle_insufficient_data(self, results: AnalysisResults) -> Dict[str, str]:
        """Handle cases with insufficient data for meaningful analysis."""
        messages = {}
        
        if results.full_moon_count == 0:
            messages['error'] = "No full moon periods found in the dataset."
            messages['suggestion'] = "Try increasing the date range to include more data."
        elif results.normal_day_count == 0:
            messages['error'] = "No normal day periods found in the dataset."
            messages['suggestion'] = "This is unusual - please check the data source."
        elif results.full_moon_count < self.min_data_points:
            messages['warning'] = f"Only {results.full_moon_count} full moon period(s) found."
            messages['suggestion'] = "Results may not be statistically significant. Consider a larger dataset."
        elif results.normal_day_count < self.min_data_points:
            messages['warning'] = f"Only {results.normal_day_count} normal day period(s) found."
            messages['suggestion'] = "Results may not be statistically significant. Consider a larger dataset."
        
        return messages
    
    def generate_summary_statistics(self, results: AnalysisResults) -> Dict[str, Any]:
        """Generate summary statistics and interpretation."""
        summary = {
            'total_periods': results.total_data_points,
            'full_moon_periods': results.full_moon_count,
            'normal_periods': results.normal_day_count,
            'full_moon_percentage': results.full_moon_percentage,
            'average_difference': results.difference
        }
        
        # Generate interpretation
        if abs(results.difference) < 0.1:
            interpretation = "No significant difference in price performance between full moon and normal days."
        elif results.difference > 0:
            interpretation = f"Cryptocurrency tends to perform {results.difference:.2f}% better on full moon days."
        else:
            interpretation = f"Cryptocurrency tends to perform {abs(results.difference):.2f}% worse on full moon days."
        
        summary['interpretation'] = interpretation
        
        return summary
# ============================================================================
# CHART RENDERER
# ============================================================================

class ChartRenderer:
    """Renderer for cryptocurrency price charts with moon phase overlays."""
    
    # Dark theme configuration
    DARK_THEME = {
        'paper_bgcolor': '#1e2139',
        'plot_bgcolor': '#2a2d5a',
        'font_color': '#e8e8e8',
        'grid_color': '#3d4465',
        'line_color': '#00d4aa'  # Bright teal for crypto line
    }
    
    # Chart layout configuration
    CHART_CONFIG = {
        'responsive': True,
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'autoScale2d']
    }
    
    def __init__(self):
        """Initialize the chart renderer."""
        self.theme = self.DARK_THEME.copy()
    
    def create_complete_chart(self, combined_data: List[CombinedDataPoint], 
                            title: str = "Cryptocurrency Price vs Moon Phases") -> go.Figure:
        """Create a complete chart with cryptocurrency prices and moon phase indicators."""
        # Create base price chart
        fig = self.create_crypto_price_chart(combined_data, title)
        
        # Add moon indicators
        fig = self.add_moon_indicators(fig, combined_data)
        
        return fig
    
    def create_crypto_price_chart(self, combined_data: List[CombinedDataPoint], 
                                 title: str = "Cryptocurrency Price Analysis") -> go.Figure:
        """Create a cryptocurrency price line chart with dark theme and interactive features."""
        if not combined_data:
            raise ValueError("No data provided for chart creation")
        
        # Validate and filter data
        valid_data = [point for point in combined_data if self._validate_data_point(point)]
        
        if not valid_data:
            raise ValueError("No valid data points found for chart creation")
        
        logger.info(f"Creating cryptocurrency price chart with {len(valid_data)} data points")
        
        # Extract data for plotting
        dates = [point.date for point in valid_data]
        prices = [point.crypto_data.close_price for point in valid_data]
        
        # Get crypto symbol for display
        crypto_symbol = valid_data[0].crypto_data.symbol if valid_data else "CRYPTO"
        
        # Create the figure
        fig = go.Figure()
        
        # Add cryptocurrency price line
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name=f'{crypto_symbol} Price',
            line=dict(
                color=self.theme['line_color'],
                width=2
            ),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                         '<b>Price:</b> $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ))
        
        # Apply dark theme and responsive design
        self._apply_chart_theme(fig, title)
        
        # Configure interactivity
        self._configure_interactivity(fig)
        
        logger.info("Cryptocurrency price chart created successfully")
        return fig
    
    def add_moon_indicators(self, fig: go.Figure, combined_data: List[CombinedDataPoint]) -> go.Figure:
        """Add golden dot overlays for full moon dates on the chart."""
        if not combined_data:
            logger.warning("No data provided for moon indicators")
            return fig
        
        # Find full moon dates and their corresponding prices
        full_moon_dates = []
        full_moon_prices = []
        full_moon_phases = []
        
        for point in combined_data:
            if (self._validate_data_point(point) and 
                point.moon_data and 
                point.moon_data.is_full_moon):
                
                full_moon_dates.append(point.date)
                full_moon_prices.append(point.crypto_data.close_price)
                full_moon_phases.append(point.moon_data.phase_percentage)
        
        if not full_moon_dates:
            logger.info("No full moon dates found in dataset")
            return fig
        
        # Add full moon indicators as scatter points
        fig.add_trace(go.Scatter(
            x=full_moon_dates,
            y=full_moon_prices,
            mode='markers',
            name='Full Moon',
            marker=dict(
                color='#fbbf24',  # Golden yellow for full moon
                size=10,
                symbol='circle',
                line=dict(
                    color='#f59e0b',
                    width=2
                )
            ),
            hovertemplate='<b>Full Moon</b><br>' +
                         '<b>Date:</b> %{x}<br>' +
                         '<b>Price:</b> $%{y:,.2f}<br>' +
                         '<b>Moon Phase:</b> %{customdata:.1f}%<br>' +
                         '<extra></extra>',
            customdata=full_moon_phases
        ))
        
        logger.info(f"Added {len(full_moon_dates)} full moon indicators to chart")
        return fig
    def _validate_data_point(self, point: CombinedDataPoint) -> bool:
        """Validate that a data point has all required fields for charting."""
        try:
            if not point or not point.date or not point.crypto_data:
                return False
            
            if not hasattr(point.crypto_data, 'close_price'):
                return False
            
            price = point.crypto_data.close_price
            if not isinstance(price, (int, float)) or price <= 0:
                return False
            
            return True
        except (AttributeError, TypeError):
            return False
    
    def _apply_chart_theme(self, fig: go.Figure, title: str) -> None:
        """Apply dark theme and responsive design to the chart."""
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(
                    size=20,
                    color=self.theme['font_color']
                ),
                x=0.5,  # Center the title
                xanchor='center'
            ),
            paper_bgcolor=self.theme['paper_bgcolor'],
            plot_bgcolor=self.theme['plot_bgcolor'],
            font=dict(
                color=self.theme['font_color'],
                family="Arial, sans-serif"
            ),
            xaxis=dict(
                title="Date",
                title_font=dict(size=14),
                tickfont=dict(size=12),
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                title="Price (USDT)",
                title_font=dict(size=14),
                tickfont=dict(size=12),
                gridcolor=self.theme['grid_color'],
                showgrid=True,
                zeroline=False,
                tickformat='$,.0f'  # Format as currency
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor=self.theme['grid_color'],
                borderwidth=1,
                font=dict(color=self.theme['font_color'])
            ),
            margin=dict(l=60, r=60, t=80, b=60)
        )
    
    def _configure_interactivity(self, fig: go.Figure) -> None:
        """Configure chart interactivity and responsiveness."""
        fig.update_layout(
            dragmode='zoom',
            selectdirection='horizontal'
        )
        
        # Enable zoom and pan
        fig.update_xaxes(fixedrange=False)
        fig.update_yaxes(fixedrange=False)
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration for Streamlit."""
        return self.CHART_CONFIG
# ============================================================================
# STREAMLIT DASHBOARD UI
# ============================================================================

class CryptoMoonDashboard:
    """Main Streamlit dashboard for Crypto Moon analysis."""
    
    def __init__(self):
        """Initialize the dashboard components."""
        self.crypto_client = CryptoDataClient()
        self.moon_calculator = MoonPhaseCalculator()
        self.data_processor = DataProcessor()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.chart_renderer = ChartRenderer()
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        
        if 'combined_data' not in st.session_state:
            st.session_state.combined_data = []
        
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        
        if 'error_message' not in st.session_state:
            st.session_state.error_message = None
        
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = None
        
        if 'selected_crypto' not in st.session_state:
            st.session_state.selected_crypto = 'Bitcoin'
    
    def run(self):
        """Run the complete dashboard application."""
        # Configure page
        st.set_page_config(
            page_title="🌙 Crypto Moon Dashboard",
            page_icon="🌙",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply enhanced dark theme CSS
        self._apply_dark_theme()
        
        # Header section
        self._render_header()
        
        # Control section with cryptocurrency selector and refresh button
        self._render_controls()
        
        # Error handling display
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
        
        # Main content
        if st.session_state.data_loaded and st.session_state.combined_data:
            self._render_main_content()
        else:
            self._render_welcome_message()
    
    def _apply_dark_theme(self):
        """Apply enhanced dark theme styling to the dashboard."""
        st.markdown("""
        <style>
        /* Main app background with dark gradient */
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e8e8e8;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Override Streamlit's default styles */
        .stApp > div {
            background: transparent;
        }
        
        /* Main header with crypto-themed gradient */
        .main-header {
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            border-radius: 20px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .main-header h1 {
            color: #ffffff !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
            font-size: 3rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        .main-header p {
            color: rgba(255,255,255,0.9) !important;
            font-size: 1.2rem !important;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
        }
        
        /* Enhanced metric containers */
        .metric-container {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            padding: 2rem;
            border-radius: 15px;
            border: 1px solid #3d4465;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00d4aa, #667eea, #764ba2);
        }
        
        .metric-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            border-color: #00d4aa;
        }
        
        .metric-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #00d4aa;
            margin-bottom: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .metric-subtitle {
            font-size: 1rem;
            color: #b8bcc8;
            opacity: 0.8;
        }
        
        /* Enhanced color scheme for changes */
        .positive-change {
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        
        .negative-change {
            color: #ff4757;
            text-shadow: 0 0 10px rgba(255, 71, 87, 0.3);
        }
        
        .neutral-change {
            color: #e8e8e8;
        }
        
        /* Enhanced data summary */
        .data-summary {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid #00d4aa;
            margin: 1rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            color: #e8e8e8;
        }
        
        /* Enhanced refresh section */
        .refresh-section {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            border: 1px solid #3d4465;
        }
        
        .refresh-section h3 {
            color: #00d4aa !important;
            margin-bottom: 1rem !important;
        }
        
        /* Enhanced selectbox styling */
        .stSelectbox > div > div {
            background-color: #2a2d5a !important;
            border: 1px solid #3d4465 !important;
            border-radius: 8px !important;
            color: #e8e8e8 !important;
        }
        
        .stSelectbox > div > div:hover {
            border-color: #00d4aa !important;
        }
        
        .stSelectbox label {
            color: #00d4aa !important;
            font-weight: bold !important;
        }
        
        /* Enhanced dataframe styling */
        .stDataFrame {
            background-color: #1e2139 !important;
        }
        
        .stDataFrame table {
            background-color: #2a2d5a !important;
            color: #e8e8e8 !important;
        }
        
        .stDataFrame th {
            background-color: #1e2139 !important;
            color: #00d4aa !important;
            font-weight: bold !important;
        }
        
        .stDataFrame td {
            background-color: #2a2d5a !important;
            color: #e8e8e8 !important;
        }
        
        /* Enhanced button styling */
        .stButton > button {
            background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%);
            color: #1a1a2e !important;
            border: none;
            border-radius: 12px;
            padding: 1rem 3rem;
            font-weight: bold;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            margin: 0 auto;
            display: block;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(0, 212, 170, 0.3);
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #00b894 0%, #009975 100%);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 212, 170, 0.5);
        }
        
        .stButton > button:active {
            transform: translateY(-1px);
        }
        
        .stButton {
            display: flex;
            justify-content: center;
            width: 100%;
        }
        
        /* Enhanced welcome message */
        .welcome-message {
            text-align: center;
            padding: 3rem;
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            border-radius: 20px;
            margin: 2rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 1px solid #3d4465;
            color: #e8e8e8;
        }
        
        .welcome-message h2 {
            color: #00d4aa !important;
            margin-bottom: 1rem !important;
        }
        
        .welcome-message p {
            color: #b8bcc8 !important;
        }
        
        /* Text color overrides */
        .stMarkdown, .stText, p, div, span {
            color: #e8e8e8 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #00d4aa !important;
        }
        
        .stMetric {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #3d4465;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .stMetric > div {
            color: #e8e8e8 !important;
        }
        
        .stMetric [data-testid="metric-container"] {
            background-color: transparent;
            border: none;
            padding: 0;
            box-shadow: none;
        }
        
        /* Enhanced error and info messages */
        .stAlert {
            border-radius: 10px;
            border: 1px solid #3d4465;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            background-color: #2a2d5a;
            color: #e8e8e8;
        }
        
        .stSuccess {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            border-left: 4px solid #00ff88;
            color: #e8e8e8;
        }
        
        .stError {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            border-left: 4px solid #ff4757;
            color: #e8e8e8;
        }
        
        .stInfo {
            background: linear-gradient(135deg, #1e2139 0%, #2a2d5a 100%);
            border-left: 4px solid #00d4aa;
            color: #e8e8e8;
        }
        
        /* Sidebar styling if used */
        .css-1d391kg {
            background-color: #1a1a2e;
        }
        </style>
        """, unsafe_allow_html=True)
    def _render_header(self):
        """Render the dashboard header."""
        st.markdown("""
        <div class="main-header">
            <h1>🌙 Crypto Moon Dashboard</h1>
            <p>Analyzing correlations between cryptocurrency price movements and lunar phases</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add helpful info about data sources
        st.info("📡 **Data Sources**: Primary (CoinGecko API) → Fallback (Demo Data). Reliable cryptocurrency data without API restrictions!")
    
    def _render_controls(self):
        """Render the control section with cryptocurrency selector and refresh button."""
        st.markdown('<div class="refresh-section">', unsafe_allow_html=True)
        
        # Cryptocurrency selector
        st.markdown("<h3 style='text-align: center; margin-bottom: 1rem;'>Select Cryptocurrency</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            crypto_options = ['Bitcoin', 'Ethereum', 'Solana']
            crypto_icons = {'Bitcoin': '₿', 'Ethereum': 'Ξ', 'Solana': '◎'}
            
            selected_crypto = st.selectbox(
                "Choose cryptocurrency:",
                crypto_options,
                index=crypto_options.index(st.session_state.selected_crypto),
                format_func=lambda x: f"{crypto_icons.get(x, '●')} {x}",
                key="crypto_selector"
            )
            
            # Update session state if selection changed
            if selected_crypto != st.session_state.selected_crypto:
                st.session_state.selected_crypto = selected_crypto
                st.session_state.data_loaded = False  # Reset data when crypto changes
                st.session_state.combined_data = []
                st.session_state.analysis_results = None
                st.session_state.error_message = None
        
        # Add some spacing
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Refresh button - properly centered
        # Dynamic button text based on data state
        if st.session_state.data_loaded:
            button_text = "🔄 Refresh Data"
            button_help = f"Fetch latest {st.session_state.selected_crypto} data and recalculate moon phases"
        else:
            button_text = "📊 Collect Data"
            button_help = f"Fetch {st.session_state.selected_crypto} data and calculate moon phases for analysis"
        
        # Center the button using columns
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(button_text, key="refresh_button", help=button_help, use_container_width=True):
                self._handle_refresh()
        
        # Display last refresh time and selected crypto
        if st.session_state.last_refresh:
            st.markdown(f"<p style='text-align: center; color: #cccccc; margin-top: 0.5rem;'>Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')} ({st.session_state.selected_crypto})</p>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _handle_refresh(self):
        """Handle the refresh button click with loading state feedback."""
        try:
            # Clear previous error
            st.session_state.error_message = None
            
            selected_crypto = st.session_state.selected_crypto
            
            # Show enhanced loading state with progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner(f"🚀 Fetching {selected_crypto} data and calculating moon phases..."):
                status_text.text("📡 Connecting to CoinGecko API...")
                progress_bar.progress(20)
                
                # Fetch cryptocurrency data
                status_text.text(f"💰 Fetching {selected_crypto} price data...")
                progress_bar.progress(40)
                crypto_data = self.crypto_client.fetch_crypto_data(selected_crypto, limit=1000)
                
                # Check data source type for user notification
                is_demo_data = False
                is_fallback_data = False
                if crypto_data and len(crypto_data) > 0:
                    latest_date = max(data.date for data in crypto_data)
                    time_diff = datetime.now() - latest_date
                    is_demo_data = time_diff.total_seconds() < 3600  # Less than 1 hour old = demo data
                    
                    # Check if we're using fallback data (CoinGecko or alternative API)
                    # This can be detected by checking if the data has certain characteristics
                    if not is_demo_data and len(crypto_data) > 0:
                        # Check if volume is the default value (indicates CoinGecko fallback)
                        first_volume = crypto_data[0].volume
                        is_fallback_data = first_volume == 1000000.0
                
                if not crypto_data:
                    progress_bar.empty()
                    status_text.empty()
                    st.session_state.error_message = f"No {selected_crypto} data received from API"
                    return
                
                # Calculate moon phases
                status_text.text("� Calculating lunar phases...")
                progress_bar.progress(60)
                dates = [data.date for data in crypto_data]
                moon_data = self.moon_calculator.calculate_moon_phases_for_dates(dates)
                
                if not moon_data:
                    progress_bar.empty()
                    status_text.empty()
                    st.session_state.error_message = "Failed to calculate moon phases"
                    return
                
                # Combine data
                status_text.text("🔗 Combining data sources...")
                progress_bar.progress(75)
                combined_data = self.data_processor.combine_data(crypto_data, moon_data)
                
                if not combined_data:
                    progress_bar.empty()
                    status_text.empty()
                    st.session_state.error_message = f"Failed to combine {selected_crypto} and moon data"
                    return
                
                # Calculate price changes
                status_text.text("📊 Analyzing price movements...")
                progress_bar.progress(85)
                combined_data_with_changes = self.data_processor.calculate_price_changes(combined_data)
                
                # Perform correlation analysis
                status_text.text("🔍 Performing correlation analysis...")
                progress_bar.progress(95)
                analysis_results = self.correlation_analyzer.analyze_correlation(combined_data_with_changes)
                
                # Update session state
                status_text.text("✅ Finalizing dashboard...")
                progress_bar.progress(100)
                st.session_state.combined_data = combined_data_with_changes
                st.session_state.analysis_results = analysis_results
                st.session_state.data_loaded = True
                st.session_state.last_refresh = datetime.now()
                
                logger.info(f"Data refresh completed successfully with {len(combined_data_with_changes)} data points for {selected_crypto}")
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show success message based on data source
                if is_demo_data:
                    st.info(f"📊 Loaded {len(combined_data_with_changes)} days of {selected_crypto} **demo data** with {analysis_results.full_moon_count} full moon periods! (CoinGecko API unavailable - using simulated data)")
                else:
                    st.success(f"🎉 Successfully loaded {len(combined_data_with_changes)} days of {selected_crypto} data from **CoinGecko API** with {analysis_results.full_moon_count} full moon periods!")
                
                # Force rerun to update the display
                st.rerun()
                
        except Exception as e:
            # Create user-friendly error messages
            error_str = str(e)
            if "403" in error_str or "forbidden" in error_str.lower():
                error_msg = (
                    "🚫 **API Access Restricted**\n\n"
                    "The cryptocurrency data API is currently blocking requests. This can happen due to:\n"
                    "- **Rate limiting**: Too many requests in a short time\n"
                    "- **IP restrictions**: Your location may be blocked\n"
                    "- **API changes**: The service may have updated their access requirements\n\n"
                    "**Solutions to try:**\n"
                    "1. Wait 5-10 minutes and try again\n"
                    "2. Use a VPN to change your IP address\n"
                    "3. Try again later when API traffic is lower\n\n"
                    "**Note:** The app will automatically try backup data sources and demo data "
                    "if the main API fails, so you can still explore the dashboard features."
                )
            elif "timeout" in error_str.lower():
                error_msg = (
                    "⏱️ **Connection Timeout**\n\n"
                    "The request took too long to complete. This usually means:\n"
                    "- Slow internet connection\n"
                    "- API server is overloaded\n\n"
                    "Please check your internet connection and try again."
                )
            elif "connection" in error_str.lower():
                error_msg = (
                    "� **Connection Error**\n\n"
                    "Unable to connect to the cryptocurrency data API. Please:\n"
                    "- Check your internet connection\n"
                    "- Try again in a few moments\n"
                    "- Ensure you're not behind a restrictive firewall"
                )
            else:
                error_msg = f"� **Data Fetch Error**\n\nFailed to refresh data: {str(e)}\n\nPlease try again in a few moments."
            
            st.session_state.error_message = error_msg
            logger.error(f"Data refresh failed: {e}")
            
            # Preserve existing data if available
            if not st.session_state.data_loaded:
                st.session_state.data_loaded = False
    def _render_main_content(self):
        """Render the main dashboard content with charts and metrics."""
        # Create chart
        try:
            selected_crypto = st.session_state.selected_crypto
            fig = self.chart_renderer.create_complete_chart(
                st.session_state.combined_data,
                title=f"{selected_crypto} Price vs Moon Phases"
            )
            
            # Display chart
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=self.chart_renderer.get_chart_config()
            )
            
        except Exception as e:
            st.error(f"Failed to render chart: {str(e)}")
            logger.error(f"Chart rendering error: {e}")
        
        # Display comparative metrics
        self._render_comparative_metrics()
        
        # Display data summary
        self._render_data_summary()
    
    def _render_comparative_metrics(self):
        """Display comparative metrics for full moon vs normal days."""
        if not st.session_state.analysis_results:
            st.warning("No analysis results available")
            return
        
        results = st.session_state.analysis_results
        
        st.markdown("## 📊 Comparative Analysis")
        
        # Check for sufficient data
        if not results.has_sufficient_data:
            insufficient_data_messages = self.correlation_analyzer.handle_insufficient_data(results)
            
            if 'error' in insufficient_data_messages:
                st.error(insufficient_data_messages['error'])
                if 'suggestion' in insufficient_data_messages:
                    st.info(insufficient_data_messages['suggestion'])
                return
            
            if 'warning' in insufficient_data_messages:
                st.warning(insufficient_data_messages['warning'])
                if 'suggestion' in insufficient_data_messages:
                    st.info(insufficient_data_messages['suggestion'])
        
        # Display metrics in columns
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_metric_card(
                title="Full Moon Days",
                value=f"{results.full_moon_avg_change:+.2f}%",
                subtitle=f"Average price change ({results.full_moon_count} days)",
                value_class=self._get_change_class(results.full_moon_avg_change)
            )
        
        with col2:
            self._render_metric_card(
                title="Normal Days",
                value=f"{results.normal_day_avg_change:+.2f}%",
                subtitle=f"Average price change ({results.normal_day_count} days)",
                value_class=self._get_change_class(results.normal_day_avg_change)
            )
        
        # Display difference
        difference = results.difference
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Difference</div>
            <div class="metric-value {self._get_change_class(difference)}">{difference:+.2f}%</div>
            <div class="metric-subtitle">Full moon days vs normal days</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display interpretation
        summary = self.correlation_analyzer.generate_summary_statistics(results)
        if 'interpretation' in summary:
            st.info(f"**Interpretation:** {summary['interpretation']}")
    
    def _render_metric_card(self, title: str, value: str, subtitle: str, value_class: str = "neutral-change"):
        """Render a metric card with styling."""
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">{title}</div>
            <div class="metric-value {value_class}">{value}</div>
            <div class="metric-subtitle">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def _get_change_class(self, change: float) -> str:
        """Get CSS class for price change styling."""
        if change > 0:
            return "positive-change"
        elif change < 0:
            return "negative-change"
        else:
            return "neutral-change"
    def _render_data_summary(self):
        """Render data summary information."""
        if not st.session_state.combined_data:
            return
        
        # Calculate summary directly from session data
        combined_data = st.session_state.combined_data
        total_points = len(combined_data)
        points_with_price_change = sum(1 for point in combined_data if point.price_change is not None)
        full_moon_points = sum(1 for point in combined_data if point.moon_data.is_full_moon)
        normal_day_points = total_points - full_moon_points
        
        st.markdown("## 📈 Data Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Data Points", total_points)
        
        with col2:
            st.metric("Full Moon Days", full_moon_points)
        
        with col3:
            st.metric("Normal Days", normal_day_points)
        
        with col4:
            st.metric("Price Changes Calculated", points_with_price_change)
        
        # Additional summary info
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            full_moon_percentage = results.full_moon_percentage
            
            st.markdown(f"""
            <div class="data-summary">
                <strong>Dataset Overview:</strong><br>
                • Full moon days represent {full_moon_percentage:.1f}% of the dataset<br>
                • Analysis covers {results.total_data_points} days with price change data<br>
                • Data spans from {combined_data[0].date.strftime('%Y-%m-%d')} to {combined_data[-1].date.strftime('%Y-%m-%d')}
            </div>
            """, unsafe_allow_html=True)
        
        # Add Full Moon Table
        self._render_full_moon_table()
    
    def _render_full_moon_table(self):
        """Render a table showing full moon dates with prices and changes."""
        if not st.session_state.combined_data:
            return
        
        # Filter full moon data
        full_moon_data = [
            point for point in st.session_state.combined_data 
            if point.moon_data.is_full_moon and point.price_change is not None
        ]
        
        if not full_moon_data:
            st.info("No full moon data with price changes available.")
            return
        
        st.markdown("## � Full Moon Analysis Table")
        
        # Create table data with enhanced formatting
        table_data = []
        for point in full_moon_data:
            # Format date with day of week
            date_str = point.date.strftime('%Y-%m-%d (%a)')
            
            # Format price change with emoji indicators
            change_val = point.price_change
            if change_val > 0:
                change_str = f"📈 +{change_val:.2f}%"
            elif change_val < 0:
                change_str = f"📉 {change_val:.2f}%"
            else:
                change_str = f"➡️ {change_val:.2f}%"
            
            table_data.append({
                "🗓️ Date": date_str,
                "� Moon Phase": f"{point.moon_data.phase_percentage:.1f}%",
                f"💰 {st.session_state.selected_crypto} Price": f"${point.crypto_data.close_price:,.2f}",
                "📊 Price Change": change_str,
                "📈 Volume": f"{point.crypto_data.volume:,.0f}"
            })
        
        # Display as dataframe with custom styling
        df = pd.DataFrame(table_data)
        
        # Style the dataframe
        def style_price_change(val):
            if isinstance(val, str) and '%' in val:
                # Extract numeric value from formatted string
                num_str = val.replace('📈', '').replace('📉', '').replace('➡️', '').replace('%', '').replace('+', '').strip()
                try:
                    num_val = float(num_str)
                    if num_val > 0:
                        return 'color: #00ff88; font-weight: bold; background-color: rgba(0, 255, 136, 0.1);'
                    elif num_val < 0:
                        return 'color: #ff4757; font-weight: bold; background-color: rgba(255, 71, 87, 0.1);'
                except ValueError:
                    pass
            return 'color: #e8e8e8;'
        
        styled_df = df.style.map(style_price_change, subset=['📊 Price Change'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Enhanced summary stats for full moon days
        if len(full_moon_data) > 0:
            avg_change = sum(point.price_change for point in full_moon_data) / len(full_moon_data)
            positive_days = sum(1 for point in full_moon_data if point.price_change > 0)
            negative_days = sum(1 for point in full_moon_data if point.price_change < 0)
            neutral_days = len(full_moon_data) - positive_days - negative_days
            
            # Calculate win rate
            win_rate = (positive_days / len(full_moon_data)) * 100
            
            st.markdown("### � Full Moon Performance Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                delta_color = "normal" if avg_change == 0 else ("inverse" if avg_change < 0 else "normal")
                st.metric(
                    "📊 Average Change", 
                    f"{avg_change:+.2f}%",
                    delta=f"{'📈' if avg_change > 0 else '📉' if avg_change < 0 else '➡️'}"
                )
            with col2:
                st.metric(
                    "🎯 Win Rate", 
                    f"{win_rate:.1f}%",
                    delta=f"{positive_days}/{len(full_moon_data)} days"
                )
            with col3:
                st.metric("📈 Positive Days", positive_days)
            with col4:
                st.metric("📉 Negative Days", negative_days)
    
    def _render_welcome_message(self):
        """Render welcome message when no data is loaded."""
        selected_crypto = st.session_state.selected_crypto
        st.markdown(f"""
        <div class="welcome-message">
            <h2>Welcome to Crypto Moon Dashboard</h2>
            <p>Select your preferred cryptocurrency above and click "Collect Data" to fetch the latest {selected_crypto} price data and begin analyzing correlations with lunar phases.</p>
            <p>The dashboard will display:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Interactive {selected_crypto} price chart with full moon indicators</li>
                <li>Comparative analysis of price changes on full moon vs normal days</li>
                <li>Statistical insights and data summaries</li>
            </ul>
            <p><strong>Supported Cryptocurrencies:</strong> Bitcoin (₿), Ethereum (Ξ), Solana (◎)</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main function to run the Crypto Moon Dashboard."""
    try:
        dashboard = CryptoMoonDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Application failed to start: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()