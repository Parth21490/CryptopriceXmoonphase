"""
Bitcoin Moon Dashboard - Main Application Entry Point

This is the main Streamlit application that analyzes correlations between
Bitcoin price movements and lunar phases. It wires together all components
from data access, business logic, and presentation layers.
"""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from presentation.dashboard_ui import DashboardUI
from config import get_config, get_component_configs

# Get application configuration
app_config = get_config()

# Configure application-wide logging
logging.basicConfig(
    level=getattr(logging, app_config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def configure_application():
    """Configure application settings and environment."""
    try:
        # Log configuration details
        logger.info("Crypto Moon Dashboard starting up...")
        logger.info(f"Debug mode: {app_config.debug}")
        logger.info(f"Log level: {app_config.log_level}")
        
        # Log component configurations
        component_configs = get_component_configs()
        logger.info("Component configurations:")
        for component, config in component_configs.items():
            logger.info(f"  {component}: {config}")
        
        logger.info("Initializing data access layer (Crypto API client, Moon calculator)")
        logger.info("Initializing business logic layer (Data processor, Correlation analyzer)")
        logger.info("Initializing presentation layer (Chart renderer, Streamlit dashboard)")
        
        return True
    except Exception as e:
        logger.error(f"Failed to configure application: {e}")
        return False


def verify_component_integration(dashboard: DashboardUI) -> bool:
    """
    Verify that all components are properly wired and accessible.
    
    Args:
        dashboard: DashboardUI instance to verify
        
    Returns:
        True if all components are properly integrated, False otherwise
    """
    try:
        # Verify data access layer components
        if not hasattr(dashboard, 'crypto_client') or dashboard.crypto_client is None:
            logger.error("CryptoDataClient not properly wired")
            return False
        
        if not hasattr(dashboard, 'moon_calculator') or dashboard.moon_calculator is None:
            logger.error("MoonPhaseCalculator not properly wired")
            return False
        
        # Verify business logic layer components
        if not hasattr(dashboard, 'data_processor') or dashboard.data_processor is None:
            logger.error("DataProcessor not properly wired")
            return False
        
        if not hasattr(dashboard, 'correlation_analyzer') or dashboard.correlation_analyzer is None:
            logger.error("CorrelationAnalyzer not properly wired")
            return False
        
        # Verify presentation layer components
        if not hasattr(dashboard, 'chart_renderer') or dashboard.chart_renderer is None:
            logger.error("ChartRenderer not properly wired")
            return False
        
        logger.info("All components verified and properly integrated")
        return True
        
    except Exception as e:
        logger.error(f"Component integration verification failed: {e}")
        return False


def create_application() -> DashboardUI:
    """
    Application factory function that creates and wires all components.
    
    This function ensures proper initialization order and component integration:
    1. Data Access Layer: BitcoinDataClient, MoonPhaseCalculator
    2. Business Logic Layer: DataProcessor, CorrelationAnalyzer  
    3. Presentation Layer: ChartRenderer, DashboardUI
    
    Returns:
        Fully configured DashboardUI instance with all components wired
    """
    try:
        logger.info("Creating application components...")
        
        # The DashboardUI constructor automatically creates and wires:
        # - CryptoDataClient for fetching crypto data (BTC, ETH, SOL) from Bybit API
        # - MoonPhaseCalculator for astronomical moon phase calculations
        # - DataProcessor for combining cryptocurrency and moon data with price changes
        # - CorrelationAnalyzer for statistical analysis of correlations
        # - ChartRenderer for creating interactive Plotly visualizations
        
        dashboard = DashboardUI()
        
        # Verify all components are properly wired
        if not verify_component_integration(dashboard):
            raise RuntimeError("Component integration verification failed")
        
        logger.info("Application components created and wired successfully")
        logger.info("Data flow: API -> Data Processing -> Analysis -> Visualization")
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise


def main():
    """
    Main application entry point.
    
    This function:
    1. Configures the application environment
    2. Creates and wires all components through the application factory
    3. Starts the Streamlit web interface
    
    The complete data flow architecture:
    ┌─────────────────────────────────────┐
    │           Presentation Layer        │
    │    DashboardUI + ChartRenderer      │
    ├─────────────────────────────────────┤
    │           Business Logic Layer      │
    │  DataProcessor + CorrelationAnalyzer│
    ├─────────────────────────────────────┤
    │            Data Access Layer        │
    │ CryptoDataClient + MoonCalculator   │
    └─────────────────────────────────────┘
    """
    try:
        # Configure application environment
        if not configure_application():
            logger.error("Application configuration failed")
            sys.exit(1)
        
        # Create application with all components wired
        dashboard = create_application()
        
        logger.info("Starting Streamlit dashboard interface...")
        dashboard.render_dashboard()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()