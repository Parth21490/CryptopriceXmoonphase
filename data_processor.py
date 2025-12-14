"""
Data Processor for combining Bitcoin and moon data.
Implements data association logic maintaining date-based relationships.
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from data_access.bitcoin_client import CryptoPriceData
from data_access.moon_calculator import MoonPhaseData

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CombinedDataPoint:
    """Combined data point containing cryptocurrency price and moon phase data."""
    date: datetime
    crypto_data: CryptoPriceData  # Renamed from bitcoin_data
    moon_data: MoonPhaseData
    price_change: Optional[float] = None
    
    # Keep backward compatibility
    @property
    def bitcoin_data(self):
        """Backward compatibility property."""
        return self.crypto_data


class DataProcessor:
    """Processor for combining cryptocurrency price data with moon phase calculations."""
    
    def __init__(self):
        """Initialize the data processor."""
        self._combined_data: List[CombinedDataPoint] = []
        self._data_cache: Dict[date, CombinedDataPoint] = {}
    
    def combine_data(self, crypto_data: List[CryptoPriceData], 
                    moon_data: List[MoonPhaseData]) -> List[CombinedDataPoint]:
        """
        Combine cryptocurrency price data with moon phase data maintaining date-based relationships.
        
        Args:
            crypto_data: List of CryptoPriceData objects
            moon_data: List of MoonPhaseData objects
            
        Returns:
            List of CombinedDataPoint objects with matching dates
            
        Raises:
            ValueError: If input data is invalid
        """
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
        """
        Calculate day-over-day price changes using the formula: 
        ((current_price - previous_price) / previous_price) * 100
        
        Args:
            combined_data: Optional list of combined data points. Uses stored data if None.
            
        Returns:
            List of CombinedDataPoint objects with price_change calculated
        """
        data_to_process = combined_data if combined_data is not None else self._combined_data
        
        if not data_to_process:
            logger.warning("No combined data available for price change calculation")
            return []
        
        # Sort by date to ensure proper order
        sorted_data = sorted(data_to_process, key=lambda x: x.date)
        
        # Calculate price changes
        processed_data = []
        previous_price = None
        
        for i, data_point in enumerate(sorted_data):
            if not data_point.crypto_data:
                logger.warning(f"Skipping data point with missing cryptocurrency data: {data_point.date}")
                continue
            
            current_price = data_point.crypto_data.close_price
            
            if previous_price is not None and previous_price != 0:
                # Calculate day-over-day percentage change
                price_change = ((current_price - previous_price) / previous_price) * 100
                data_point.price_change = price_change
            else:
                # First data point or previous price is zero
                data_point.price_change = None
            
            processed_data.append(data_point)
            previous_price = current_price
        
        logger.info(f"Calculated price changes for {len(processed_data)} data points")
        
        # Update stored data
        self._combined_data = processed_data
        self._update_cache(processed_data)
        
        return processed_data
    
    def get_data_by_date_range(self, start_date: datetime, end_date: datetime) -> List[CombinedDataPoint]:
        """
        Retrieve combined data points within a specific date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of CombinedDataPoint objects within the date range
        """
        if not self._combined_data:
            logger.warning("No combined data available for date range query")
            return []
        
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
        
        filtered_data = [
            data_point for data_point in self._combined_data
            if start_date <= data_point.date <= end_date
        ]
        
        logger.info(f"Retrieved {len(filtered_data)} data points for date range "
                   f"{start_date.date()} to {end_date.date()}")
        
        return filtered_data
    
    def get_data_by_date(self, target_date: date) -> Optional[CombinedDataPoint]:
        """
        Retrieve a specific data point by date.
        
        Args:
            target_date: The date to look up
            
        Returns:
            CombinedDataPoint for the date, or None if not found
        """
        return self._data_cache.get(target_date)
    
    def store_data(self, combined_data: List[CombinedDataPoint]) -> None:
        """
        Store combined data points for later retrieval.
        
        Args:
            combined_data: List of CombinedDataPoint objects to store
        """
        if not combined_data:
            logger.warning("No data provided for storage")
            return
        
        self._combined_data = combined_data.copy()
        self._update_cache(combined_data)
        
        logger.info(f"Stored {len(combined_data)} combined data points")
    
    def retrieve_all_data(self) -> List[CombinedDataPoint]:
        """
        Retrieve all stored combined data points.
        
        Returns:
            List of all stored CombinedDataPoint objects
        """
        return self._combined_data.copy()
    
    def clear_data(self) -> None:
        """Clear all stored data."""
        self._combined_data.clear()
        self._data_cache.clear()
        logger.info("Cleared all stored data")
    
    def get_data_summary(self) -> Dict[str, int]:
        """
        Get summary statistics about stored data.
        
        Returns:
            Dictionary with summary statistics
        """
        total_points = len(self._combined_data)
        points_with_price_change = sum(1 for point in self._combined_data if point.price_change is not None)
        full_moon_points = sum(1 for point in self._combined_data if point.moon_data.is_full_moon)
        
        return {
            'total_points': total_points,
            'points_with_price_change': points_with_price_change,
            'full_moon_points': full_moon_points,
            'normal_day_points': total_points - full_moon_points
        }
    
    def _update_cache(self, combined_data: List[CombinedDataPoint]) -> None:
        """
        Update the internal cache with combined data points.
        
        Args:
            combined_data: List of CombinedDataPoint objects
        """
        self._data_cache.clear()
        for data_point in combined_data:
            if data_point and data_point.date:
                date_key = data_point.date.date()
                self._data_cache[date_key] = data_point
    
    def validate_combined_data(self, combined_data: List[CombinedDataPoint]) -> Tuple[bool, List[str]]:
        """
        Validate combined data for consistency and completeness.
        
        Args:
            combined_data: List of CombinedDataPoint objects to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        if not combined_data:
            return False, ["No data provided for validation"]
        
        errors = []
        
        for i, data_point in enumerate(combined_data):
            if not data_point:
                errors.append(f"Data point {i} is None")
                continue
            
            if not data_point.date:
                errors.append(f"Data point {i} has no date")
            
            if not data_point.crypto_data:
                errors.append(f"Data point {i} has no cryptocurrency data")
            
            if not data_point.moon_data:
                errors.append(f"Data point {i} has no moon data")
            
            # Check date consistency
            if (data_point.date and data_point.crypto_data and data_point.crypto_data.date and
                data_point.date.date() != data_point.crypto_data.date.date()):
                errors.append(f"Data point {i} has mismatched cryptocurrency date")
            
            if (data_point.date and data_point.moon_data and data_point.moon_data.date and
                data_point.date.date() != data_point.moon_data.date.date()):
                errors.append(f"Data point {i} has mismatched moon data date")
        
        is_valid = len(errors) == 0
        return is_valid, errors