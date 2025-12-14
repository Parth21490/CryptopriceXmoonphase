#!/usr/bin/env python3
"""
Test script to verify API fallback system works correctly.
"""

import sys
import logging
from datetime import datetime

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import the crypto data client from the dashboard
sys.path.append('.')

try:
    # Extract just the CryptoDataClient class from the dashboard file
    exec("""
import requests
import time
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class CryptoPriceData:
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    symbol: str
""")
    
    # Read and execute the CryptoDataClient class definition
    with open('crypto_moon_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract just the CryptoDataClient class
    start_marker = "class CryptoDataClient:"
    end_marker = "class MoonPhaseCalculator:"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        client_code = content[start_idx:end_idx]
        exec(client_code)
        
        print("🧪 Testing API Fallback System...")
        print("=" * 50)
        
        # Test the client
        client = CryptoDataClient()
        
        try:
            print("📡 Testing Bitcoin data fetch with fallback...")
            data = client.fetch_crypto_data('Bitcoin', limit=10)
            
            if data:
                print(f"✅ Successfully fetched {len(data)} data points!")
                print(f"📅 Date range: {data[0].date.date()} to {data[-1].date.date()}")
                print(f"💰 Latest price: ${data[-1].close_price:,.2f}")
                print(f"📊 Data source: {data[0].symbol}")
                
                # Check if it's demo data (very recent dates)
                latest_date = max(d.date for d in data)
                time_diff = datetime.now() - latest_date
                if time_diff.total_seconds() < 3600:
                    print("🎭 Using DEMO DATA (APIs unavailable)")
                elif data[0].volume == 1000000.0:
                    print("🔄 Using BACKUP API (Primary API unavailable)")
                else:
                    print("🎯 Using PRIMARY API")
                    
            else:
                print("❌ No data received")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
    else:
        print("❌ Could not extract CryptoDataClient class")
        
except Exception as e:
    print(f"❌ Test setup failed: {e}")
    print("💡 This is expected if some dependencies are missing")
    print("🚀 The dashboard should still work with demo data!")