"""
Correlation Analyzer for statistical analysis of Bitcoin price movements and moon phases.
Implements average calculation for full moon vs normal days with handling for insufficient data.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
from statistics import mean

from business_logic.data_processor import CombinedDataPoint

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResults:
    """Results of correlation analysis between Bitcoin prices and moon phases."""
    full_moon_avg_change: float
    normal_day_avg_change: float
    full_moon_count: int
    normal_day_count: int
    total_data_points: int
    
    @property
    def has_sufficient_data(self) -> bool:
        """Check if there's sufficient data for meaningful analysis."""
        return self.full_moon_count >= 1 and self.normal_day_count >= 1
    
    @property
    def full_moon_percentage(self) -> float:
        """Calculate percentage of full moon days in dataset."""
        if self.total_data_points == 0:
            return 0.0
        return (self.full_moon_count / self.total_data_points) * 100
    
    @property
    def difference(self) -> float:
        """Calculate difference between full moon and normal day averages."""
        return self.full_moon_avg_change - self.normal_day_avg_change


class CorrelationAnalyzer:
    """Analyzer for statistical correlation between Bitcoin prices and moon phases."""
    
    def __init__(self):
        """Initialize the correlation analyzer."""
        self.min_data_points = 1  # Minimum data points required for each category
    
    def analyze_correlation(self, combined_data: List[CombinedDataPoint]) -> AnalysisResults:
        """
        Analyze correlation between Bitcoin price changes and moon phases.
        
        Args:
            combined_data: List of CombinedDataPoint objects with price changes
            
        Returns:
            AnalysisResults object containing statistical analysis
            
        Raises:
            ValueError: If input data is invalid
        """
        if not combined_data:
            logger.warning("No data provided for correlation analysis")
            return AnalysisResults(
                full_moon_avg_change=0.0,
                normal_day_avg_change=0.0,
                full_moon_count=0,
                normal_day_count=0,
                total_data_points=0
            )
        
        # Filter data points that have price changes calculated
        valid_data = [
            point for point in combined_data 
            if point.price_change is not None and 
               point.bitcoin_data is not None and 
               point.moon_data is not None
        ]
        
        if not valid_data:
            logger.warning("No valid data points with price changes for analysis")
            return AnalysisResults(
                full_moon_avg_change=0.0,
                normal_day_avg_change=0.0,
                full_moon_count=0,
                normal_day_count=0,
                total_data_points=len(combined_data)
            )
        
        # Separate full moon days from normal days
        full_moon_changes = []
        normal_day_changes = []
        
        for point in valid_data:
            if point.moon_data.is_full_moon:  # moon_phase > 98%
                full_moon_changes.append(point.price_change)
            else:
                normal_day_changes.append(point.price_change)
        
        # Calculate averages
        full_moon_avg = self._calculate_average(full_moon_changes)
        normal_day_avg = self._calculate_average(normal_day_changes)
        
        results = AnalysisResults(
            full_moon_avg_change=full_moon_avg,
            normal_day_avg_change=normal_day_avg,
            full_moon_count=len(full_moon_changes),
            normal_day_count=len(normal_day_changes),
            total_data_points=len(valid_data)
        )
        
        logger.info(f"Correlation analysis complete: {len(full_moon_changes)} full moon days, "
                   f"{len(normal_day_changes)} normal days")
        
        return results
    
    def _calculate_average(self, values: List[float]) -> float:
        """
        Calculate average of a list of values, handling empty lists.
        
        Args:
            values: List of numeric values
            
        Returns:
            Average value, or 0.0 if list is empty
        """
        if not values:
            return 0.0
        
        try:
            return mean(values)
        except Exception as e:
            logger.error(f"Failed to calculate average: {e}")
            return 0.0
    
    def generate_summary_statistics(self, results: AnalysisResults) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics from analysis results.
        
        Args:
            results: AnalysisResults object
            
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'total_data_points': results.total_data_points,
            'full_moon_count': results.full_moon_count,
            'normal_day_count': results.normal_day_count,
            'full_moon_percentage': results.full_moon_percentage,
            'full_moon_avg_change': results.full_moon_avg_change,
            'normal_day_avg_change': results.normal_day_avg_change,
            'difference': results.difference,
            'has_sufficient_data': results.has_sufficient_data
        }
        
        # Add interpretation
        if results.has_sufficient_data:
            if abs(results.difference) < 0.1:
                summary['interpretation'] = 'No significant difference detected'
            elif results.full_moon_avg_change > results.normal_day_avg_change:
                summary['interpretation'] = 'Full moon days show higher average price changes'
            else:
                summary['interpretation'] = 'Normal days show higher average price changes'
        else:
            summary['interpretation'] = 'Insufficient data for meaningful analysis'
        
        return summary
    
    def handle_insufficient_data(self, results: AnalysisResults) -> Dict[str, str]:
        """
        Handle scenarios with insufficient data and provide appropriate messages.
        
        Args:
            results: AnalysisResults object
            
        Returns:
            Dictionary containing appropriate messages for insufficient data scenarios
        """
        messages = {}
        
        if results.total_data_points == 0:
            messages['error'] = 'No data available for analysis'
            messages['suggestion'] = 'Please fetch Bitcoin price data first'
            return messages
        
        if results.full_moon_count == 0:
            messages['warning'] = 'No full moon periods found in dataset'
            messages['suggestion'] = (
                f'Dataset contains {results.total_data_points} data points but no full moon days. '
                'Consider expanding the date range to include full moon periods.'
            )
        
        if results.normal_day_count == 0:
            messages['warning'] = 'No normal days found in dataset'
            messages['suggestion'] = (
                'Dataset contains only full moon days. This is unusual and may indicate '
                'a data filtering issue.'
            )
        
        if results.full_moon_count < self.min_data_points:
            messages['info'] = f'Limited full moon data ({results.full_moon_count} days)'
            messages['suggestion'] = (
                'Results may be less reliable with limited full moon data. '
                'Consider expanding the dataset for more robust analysis.'
            )
        
        if results.normal_day_count < 10:  # Arbitrary threshold for normal days
            messages['info'] = f'Limited normal day data ({results.normal_day_count} days)'
            messages['suggestion'] = (
                'More normal day data would improve analysis reliability.'
            )
        
        return messages
    
    def validate_analysis_input(self, combined_data: List[CombinedDataPoint]) -> tuple[bool, List[str]]:
        """
        Validate input data for correlation analysis.
        
        Args:
            combined_data: List of CombinedDataPoint objects
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        if not combined_data:
            return False, ["No data provided for analysis"]
        
        errors = []
        valid_points = 0
        
        for i, point in enumerate(combined_data):
            if not point:
                errors.append(f"Data point {i} is None")
                continue
            
            if not point.bitcoin_data:
                errors.append(f"Data point {i} missing Bitcoin data")
                continue
            
            if not point.moon_data:
                errors.append(f"Data point {i} missing moon data")
                continue
            
            if point.price_change is None:
                # This is not an error, just means it's the first data point
                continue
            
            if not isinstance(point.price_change, (int, float)):
                errors.append(f"Data point {i} has invalid price change type")
                continue
            
            valid_points += 1
        
        if valid_points == 0:
            errors.append("No valid data points found for analysis")
        
        is_valid = len(errors) == 0 and valid_points > 0
        return is_valid, errors
    
    def compare_periods(self, results: AnalysisResults) -> Dict[str, Any]:
        """
        Compare full moon and normal day periods with statistical context.
        
        Args:
            results: AnalysisResults object
            
        Returns:
            Dictionary containing comparison analysis
        """
        if not results.has_sufficient_data:
            return {
                'comparison_available': False,
                'message': 'Insufficient data for period comparison'
            }
        
        comparison = {
            'comparison_available': True,
            'full_moon_performance': {
                'average_change': results.full_moon_avg_change,
                'sample_size': results.full_moon_count,
                'percentage_of_dataset': results.full_moon_percentage
            },
            'normal_day_performance': {
                'average_change': results.normal_day_avg_change,
                'sample_size': results.normal_day_count,
                'percentage_of_dataset': 100.0 - results.full_moon_percentage
            },
            'difference': results.difference,
            'absolute_difference': abs(results.difference)
        }
        
        # Add relative performance indicator
        if results.difference > 0:
            comparison['better_performer'] = 'full_moon'
            comparison['performance_ratio'] = (
                results.full_moon_avg_change / results.normal_day_avg_change 
                if results.normal_day_avg_change != 0 else float('inf')
            )
        elif results.difference < 0:
            comparison['better_performer'] = 'normal_days'
            comparison['performance_ratio'] = (
                results.normal_day_avg_change / results.full_moon_avg_change 
                if results.full_moon_avg_change != 0 else float('inf')
            )
        else:
            comparison['better_performer'] = 'equal'
            comparison['performance_ratio'] = 1.0
        
        return comparison