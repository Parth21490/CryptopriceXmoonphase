"""
Moon Phase Calculator for astronomical calculations.
Implements moon phase calculation for given dates with normalization to 0-100% scale.
"""

import math
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import logging

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MoonPhaseData:
    """Data model for moon phase information."""
    date: datetime
    phase_percentage: float  # 0-100%
    
    @property
    def is_full_moon(self) -> bool:
        """Check if this represents a full moon (>98% illumination)."""
        return self.phase_percentage > 98.0


class MoonPhaseCalculator:
    """Calculator for moon phases using astronomical formulas."""
    
    # Known new moon reference point (January 6, 2000, 18:14 UTC)
    NEW_MOON_REFERENCE = datetime(2000, 1, 6, 18, 14, 0)
    LUNAR_CYCLE_DAYS = 29.530588853  # Average lunar cycle length in days
    
    def __init__(self):
        """Initialize the moon phase calculator."""
        pass
    
    def calculate_moon_phase(self, date: datetime) -> Optional[MoonPhaseData]:
        """
        Calculate moon phase percentage for a given date.
        
        Args:
            date: The date to calculate moon phase for
            
        Returns:
            MoonPhaseData object with phase percentage, or None if calculation fails
            
        Raises:
            ValueError: If date is invalid
        """
        try:
            if date is None:
                raise ValueError("Date cannot be None")
            
            # Calculate days since reference new moon
            time_diff = date - self.NEW_MOON_REFERENCE
            days_since_reference = time_diff.total_seconds() / (24 * 3600)
            
            # Calculate current position in lunar cycle
            cycles_elapsed = days_since_reference / self.LUNAR_CYCLE_DAYS
            cycle_position = cycles_elapsed - math.floor(cycles_elapsed)
            
            # Convert cycle position to phase percentage
            # 0.0 = New Moon (0%), 0.5 = Full Moon (100%), 1.0 = New Moon (0%)
            if cycle_position <= 0.5:
                # Waxing phase: 0% to 100%
                phase_percentage = cycle_position * 200.0
            else:
                # Waning phase: 100% to 0%
                phase_percentage = (1.0 - cycle_position) * 200.0
            
            # Ensure percentage is within valid range
            phase_percentage = max(0.0, min(100.0, phase_percentage))
            
            logger.debug(f"Moon phase for {date.date()}: {phase_percentage:.2f}%")
            
            return MoonPhaseData(
                date=date,
                phase_percentage=phase_percentage
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate moon phase for {date}: {e}")
            return None
    
    def calculate_moon_phases_for_dates(self, dates: list[datetime]) -> list[MoonPhaseData]:
        """
        Calculate moon phases for multiple dates.
        
        Args:
            dates: List of dates to calculate moon phases for
            
        Returns:
            List of MoonPhaseData objects (excludes failed calculations)
        """
        if not dates:
            return []
        
        moon_phases = []
        failed_count = 0
        
        for date in dates:
            try:
                phase_data = self.calculate_moon_phase(date)
                if phase_data is not None:
                    moon_phases.append(phase_data)
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"Failed to calculate moon phase for {date}: {e}")
                failed_count += 1
                continue
        
        if failed_count > 0:
            logger.warning(f"Failed to calculate moon phases for {failed_count} dates")
        
        logger.info(f"Successfully calculated moon phases for {len(moon_phases)} dates")
        return moon_phases
    
    def find_full_moon_dates(self, moon_phases: list[MoonPhaseData]) -> list[MoonPhaseData]:
        """
        Identify dates with full moon phases (>98% illumination).
        
        Args:
            moon_phases: List of MoonPhaseData objects
            
        Returns:
            List of MoonPhaseData objects representing full moon dates
        """
        if not moon_phases:
            return []
        
        full_moons = [phase for phase in moon_phases if phase.is_full_moon]
        
        logger.info(f"Found {len(full_moons)} full moon dates out of {len(moon_phases)} total dates")
        return full_moons
    
    def normalize_phase_percentage(self, raw_percentage: float) -> float:
        """
        Normalize phase percentage to 0-100% scale.
        
        Args:
            raw_percentage: Raw percentage value
            
        Returns:
            Normalized percentage between 0.0 and 100.0
        """
        if raw_percentage is None or math.isnan(raw_percentage) or math.isinf(raw_percentage):
            return 0.0
        
        return max(0.0, min(100.0, float(raw_percentage)))
    
    def validate_moon_phase_data(self, phase_data: MoonPhaseData) -> bool:
        """
        Validate moon phase data for correctness.
        
        Args:
            phase_data: MoonPhaseData object to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if phase_data is None:
                return False
            
            if phase_data.date is None:
                return False
            
            if not isinstance(phase_data.phase_percentage, (int, float)):
                return False
            
            if math.isnan(phase_data.phase_percentage) or math.isinf(phase_data.phase_percentage):
                return False
            
            if phase_data.phase_percentage < 0.0 or phase_data.phase_percentage > 100.0:
                return False
            
            return True
            
        except (AttributeError, TypeError):
            return False