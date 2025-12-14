"""
Chart Renderer for Plotly visualizations.
Implements Bitcoin price line chart with dark theme and interactive features.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from business_logic.data_processor import CombinedDataPoint

# Configure logging
logger = logging.getLogger(__name__)


class ChartRenderer:
    """Renderer for Bitcoin price charts with moon phase overlays."""
    
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
    
    def create_crypto_price_chart(self, combined_data: List[CombinedDataPoint], 
                                 title: str = "Cryptocurrency Price Analysis") -> go.Figure:
        """
        Create a cryptocurrency price line chart with dark theme and interactive features.
        
        Args:
            combined_data: List of CombinedDataPoint objects with cryptocurrency price data
            title: Chart title
            
        Returns:
            Plotly Figure object with cryptocurrency price chart
            
        Raises:
            ValueError: If data is invalid or empty
        """
        if not combined_data:
            raise ValueError("No data provided for chart creation")
        
        # Validate data
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
        """
        Add white dot overlays for full moon dates on the chart.
        
        Args:
            fig: Existing Plotly figure to add indicators to
            combined_data: List of CombinedDataPoint objects
            
        Returns:
            Updated Plotly Figure with moon indicators
        """
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
    
    def create_complete_chart(self, combined_data: List[CombinedDataPoint], 
                            title: str = "Cryptocurrency Price vs Moon Phases") -> go.Figure:
        """
        Create a complete chart with cryptocurrency prices and moon phase indicators.
        
        Args:
            combined_data: List of CombinedDataPoint objects
            title: Chart title
            
        Returns:
            Complete Plotly Figure with price line and moon indicators
        """
        # Create base price chart
        fig = self.create_crypto_price_chart(combined_data, title)
        
        # Add moon indicators
        fig = self.add_moon_indicators(fig, combined_data)
        
        return fig
    
    # Backward compatibility
    def create_bitcoin_price_chart(self, combined_data: List[CombinedDataPoint], 
                                 title: str = "Bitcoin Price Analysis") -> go.Figure:
        """Backward compatibility method."""
        return self.create_crypto_price_chart(combined_data, title)
    
    def _validate_data_point(self, point: CombinedDataPoint) -> bool:
        """
        Validate that a data point has all required fields for charting.
        
        Args:
            point: CombinedDataPoint to validate
            
        Returns:
            True if valid, False otherwise
        """
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
        """
        Apply dark theme and responsive design to the chart.
        
        Args:
            fig: Plotly figure to style
            title: Chart title
        """
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
            # Responsive design
            autosize=True,
            margin=dict(l=60, r=30, t=60, b=60)
        )
    
    def _configure_interactivity(self, fig: go.Figure) -> None:
        """
        Configure interactive features for the chart.
        
        Args:
            fig: Plotly figure to configure
        """
        fig.update_layout(
            # Enable zoom and pan
            dragmode='zoom',
            # Configure selection tools
            selectdirection='h'  # 'h' for horizontal, 'v' for vertical, 'd' for diagonal, 'any' for any
        )
        
        # Update x-axis for better interaction
        fig.update_xaxes(
            rangeslider_visible=False,  # Disable range slider for cleaner look
            type='date'
        )
    
    def get_chart_config(self) -> Dict[str, Any]:
        """
        Get chart configuration for Streamlit display.
        
        Returns:
            Configuration dictionary for Plotly charts
        """
        return self.CHART_CONFIG.copy()
    
    def update_theme(self, theme_updates: Dict[str, str]) -> None:
        """
        Update the chart theme with custom colors.
        
        Args:
            theme_updates: Dictionary of theme property updates
        """
        self.theme.update(theme_updates)
        logger.info("Chart theme updated")
    
    def create_responsive_layout(self, width_breakpoint: int = 768) -> Dict[str, Any]:
        """
        Create responsive layout configuration based on screen width.
        
        Args:
            width_breakpoint: Pixel width to determine mobile vs desktop layout
            
        Returns:
            Layout configuration dictionary
        """
        # This would typically be used with JavaScript in a real implementation
        # For now, return a configuration that works well across screen sizes
        return {
            'autosize': True,
            'responsive': True,
            'margin': dict(
                l=50 if width_breakpoint < 768 else 60,
                r=20 if width_breakpoint < 768 else 30,
                t=50 if width_breakpoint < 768 else 60,
                b=50 if width_breakpoint < 768 else 60
            ),
            'font': dict(
                size=10 if width_breakpoint < 768 else 12
            )
        }