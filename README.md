# 🌙 Crypto Moon Dashboard

A beautiful, interactive dashboard that analyzes correlations between cryptocurrency price movements and lunar phases. Built with Streamlit and featuring real-time data from multiple crypto exchanges.

![Dashboard Preview](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)

## ✨ Features

- 🪙 **Multi-Cryptocurrency Support**: Bitcoin (₿), Ethereum (Ξ), and Solana (◎)
- 🌙 **Lunar Phase Analysis**: Real-time astronomical calculations
- 📊 **Interactive Charts**: Dark-themed visualizations with full moon indicators
- 📈 **Statistical Analysis**: Correlation metrics and performance comparisons
- 🌕 **Full Moon Table**: Detailed breakdown of price movements during full moons
- 🎨 **Beautiful Dark Theme**: Professional crypto-themed interface
- 📱 **Responsive Design**: Works on desktop and mobile devices

## 🚀 Live Demo

**[Launch Dashboard](https://your-app-name.streamlit.app)** ← Click to try it live!

## 📸 Screenshots

### Main Dashboard
![Main Dashboard](https://via.placeholder.com/800x400/1e2139/00d4aa?text=Crypto+Moon+Dashboard)

### Full Moon Analysis
![Full Moon Table](https://via.placeholder.com/800x300/2a2d5a/ffffff?text=Full+Moon+Analysis+Table)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crypto-moon-dashboard.git
   cd crypto-moon-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**
   ```bash
   streamlit run main.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501`

## 🌐 Deploy to Streamlit Cloud

1. **Fork this repository** to your GitHub account

2. **Visit [Streamlit Cloud](https://streamlit.io/cloud)**

3. **Connect your GitHub account** and select this repository

4. **Set the main file path**: `main.py`

5. **Deploy!** Your app will be live at `https://your-app-name.streamlit.app`

## 📊 How It Works

### Data Sources
- **Cryptocurrency Data**: Real-time price data from Bybit API
- **Lunar Data**: Astronomical calculations using PyEphem library
- **Analysis**: Statistical correlation analysis between moon phases and price movements

### Architecture
```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│         (Streamlit Dashboard)       │
├─────────────────────────────────────┤
│           Business Logic Layer      │
│    (Data Processing & Analysis)     │
├─────────────────────────────────────┤
│            Data Access Layer        │
│     (API Client & Moon Calculator)  │
└─────────────────────────────────────┘
```

## 🔧 Configuration

The dashboard uses the following configuration (in `config.py`):

- **API Settings**: Rate limiting, timeouts, data limits
- **Moon Phase Threshold**: 98% illumination for "full moon"
- **Chart Settings**: Dark theme, responsive breakpoints
- **Analysis Parameters**: Minimum data points for correlation

## 📈 Features in Detail

### Cryptocurrency Selection
Choose from three major cryptocurrencies:
- **Bitcoin (BTC)**: The original cryptocurrency
- **Ethereum (ETH)**: Smart contract platform
- **Solana (SOL)**: High-performance blockchain

### Moon Phase Analysis
- Calculates precise lunar phases for each date
- Identifies full moon periods (>98% illumination)
- Correlates moon phases with price movements
- Provides statistical significance testing

### Interactive Visualizations
- **Price Charts**: Interactive Plotly charts with zoom and pan
- **Moon Indicators**: Golden dots marking full moon dates
- **Performance Metrics**: Win rates, averages, and comparisons
- **Data Table**: Detailed breakdown of full moon trading days

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run property-based tests
pytest tests/ -v --hypothesis-show-statistics
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Bybit API** for cryptocurrency data
- **PyEphem** for astronomical calculations
- **Streamlit** for the amazing web framework
- **Plotly** for interactive visualizations

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/crypto-moon-dashboard/issues) page
2. Create a new issue with detailed information
3. Join our [Discussions](https://github.com/yourusername/crypto-moon-dashboard/discussions)

---

**Made with ❤️ and 🌙 by [Your Name]**

*Disclaimer: This dashboard is for educational and research purposes only. Cryptocurrency trading involves significant risk. Past performance does not guarantee future results.*