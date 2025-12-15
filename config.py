"""
Configuration module for Bitcoin Moon Dashboard.
Centralizes application settings and component configuration.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class APIConfig:
    """Configuration for external API connections."""
    bybit_base_url: str = "https://api.bybit.com"
    rate_limit_delay: float = 0.1  # seconds between requests
    request_timeout: int = 30  # seconds
    max_data_points: int = 1000


@dataclass
class AnalysisConfig:
    """Configuration for data analysis parameters."""
    full_moon_threshold: float = 98.0  # percentage for full moon identification
    min_data_points_for_analysis: int = 1
    lunar_cycle_days: float = 29.530588853


@dataclass
class UIConfig:
    """Configuration for user interface settings."""
    page_title: str = "Crypto Moon Dashboard"
    page_icon: str = "🌙"
    layout: str = "wide"
    theme: str = "professional"
    chart_height: int = 600
    responsive_breakpoint: int = 768  # pixels


@dataclass
class AppConfig:
    """Main application configuration."""
    api: APIConfig
    analysis: AnalysisConfig
    ui: UIConfig
    debug: bool = False
    log_level: str = "INFO"
    
    def __init__(self):
        """Initialize configuration with environment variable overrides."""
        self.api = APIConfig()
        self.analysis = AnalysisConfig()
        self.ui = UIConfig()
        
        # Override with environment variables if present
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # API configuration overrides
        if os.getenv('BYBIT_BASE_URL'):
            self.api.bybit_base_url = os.getenv('BYBIT_BASE_URL')
        
        if os.getenv('API_RATE_LIMIT'):
            try:
                self.api.rate_limit_delay = float(os.getenv('API_RATE_LIMIT'))
            except ValueError:
                pass
        
        # Analysis configuration overrides
        if os.getenv('FULL_MOON_THRESHOLD'):
            try:
                self.analysis.full_moon_threshold = float(os.getenv('FULL_MOON_THRESHOLD'))
            except ValueError:
                pass


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global application configuration."""
    return config


def update_config(**kwargs) -> None:
    """Update configuration values."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)


def get_component_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get configuration dictionaries for all components.
    
    Returns:
        Dictionary mapping component names to their configuration
    """
    return {
        'bitcoin_client': {
            'base_url': config.api.bybit_base_url,
            'rate_limit_delay': config.api.rate_limit_delay,
            'timeout': config.api.request_timeout,
            'max_limit': config.api.max_data_points
        },
        'moon_calculator': {
            'lunar_cycle_days': config.analysis.lunar_cycle_days
        },
        'correlation_analyzer': {
            'full_moon_threshold': config.analysis.full_moon_threshold,
            'min_data_points': config.analysis.min_data_points_for_analysis
        },
        'dashboard_ui': {
            'page_title': config.ui.page_title,
            'page_icon': config.ui.page_icon,
            'layout': config.ui.layout,
            'theme': config.ui.theme
        },
        'chart_renderer': {
            'height': config.ui.chart_height,
            'responsive_breakpoint': config.ui.responsive_breakpoint
        }
    }