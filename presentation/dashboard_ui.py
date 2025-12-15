"""
Dashboard UI with Streamlit for Bitcoin Moon Dashboard.
Implements main dashboard interface with dark theme, refresh functionality, and comparative metrics.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from data_access.bitcoin_client import CryptoDataClient
from data_access.moon_calculator import MoonPhaseCalculator
from business_logic.data_processor import DataProcessor
from business_logic.correlation_analyzer import CorrelationAnalyzer
from presentation.chart_renderer import ChartRenderer

# Configure logging
logger = logging.getLogger(__name__)


class DashboardUI:
    """Streamlit-based dashboard interface for Bitcoin Moon analysis."""
    
    def __init__(self):
        """Initialize the dashboard UI components."""
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
    
    def render_dashboard(self):
        """Render the complete dashboard interface."""
        # Configure page
        st.set_page_config(
            page_title="Crypto Moon Dashboard",
            page_icon="🌙",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply enhanced dark theme CSS
        self._apply_dark_theme()
        
        # Header section
        self._render_header()
        
        # Control section with refresh button
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
        
        .stWarning {
            background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
            border-left: 4px solid #f59e0b;
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
        
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            # Dynamic button text based on data state
            if st.session_state.data_loaded:
                button_text = "🔄 Refresh Data"
                button_help = f"Fetch latest {st.session_state.selected_crypto} data and recalculate moon phases"
            else:
                button_text = "📊 Collect Data"
                button_help = f"Fetch {st.session_state.selected_crypto} data and calculate moon phases for analysis"
            
            if st.button(button_text, key="refresh_button", help=button_help, width='stretch'):
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
                status_text.text("📡 Connecting to Bybit API...")
                progress_bar.progress(20)
                # Fetch cryptocurrency data
                status_text.text(f"💰 Fetching {selected_crypto} price data...")
                progress_bar.progress(40)
                crypto_data = self.crypto_client.fetch_crypto_data(selected_crypto, limit=1000)
                
                if not crypto_data:
                    progress_bar.empty()
                    status_text.empty()
                    st.session_state.error_message = f"No {selected_crypto} data received from API"
                    return
                
                # Calculate moon phases
                status_text.text("🌙 Calculating lunar phases...")
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
                
                # Show success message
                st.success(f"🎉 Successfully loaded {len(combined_data_with_changes)} days of {selected_crypto} data with {analysis_results.full_moon_count} full moon periods!")
                
                # Force rerun to update the display
                st.rerun()
                
        except Exception as e:
            error_msg = f"Failed to refresh data: {str(e)}"
            st.session_state.error_message = error_msg
            logger.error(error_msg)
            
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
                width='stretch',
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
        
        st.markdown("## 🌕 Full Moon Analysis Table")
        
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
                "🌕 Moon Phase": f"{point.moon_data.phase_percentage:.1f}%",
                f"💰 {st.session_state.selected_crypto} Price": f"${point.crypto_data.close_price:,.2f}",
                "📊 Price Change": change_str,
                "📈 Volume": f"{point.crypto_data.volume:,.0f}"
            })
        
        # Display as dataframe with custom styling
        import pandas as pd
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
            width='stretch',
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
            
            st.markdown("### 🌕 Full Moon Performance Summary")
            
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
    
    def render_error_handling(self, error_message: str):
        """Render user-friendly error messages."""
        st.error(f"⚠️ {error_message}")
        
        # Provide helpful suggestions based on error type
        if "API" in error_message or "request" in error_message.lower():
            st.info("💡 **Suggestion:** This might be a temporary network issue. Please try refreshing the data again in a few moments.")
        elif "data" in error_message.lower():
            st.info("💡 **Suggestion:** There might be an issue with the data format. The existing visualization will be preserved if available.")
        else:
            st.info("💡 **Suggestion:** Please try refreshing the page or contact support if the issue persists.")


def main():
    """Main function to run the dashboard."""
    dashboard = DashboardUI()
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()