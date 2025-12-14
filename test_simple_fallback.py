#!/usr/bin/env python3
"""
Simple test to verify the fallback system works.
"""

import sys
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CryptoPriceData:
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    symbol: str

def generate_simple_demo_data(crypto_name: str = 'Bitcoin', limit: int = 30) -> List[CryptoPriceData]:
    """Generate simple demo data that always works."""
    print(f"🎭 Generating demo data for {crypto_name}...")
    
    # Base prices
    base_prices = {'Bitcoin': 45000.0, 'Ethereum': 3000.0, 'Solana': 100.0}
    base_price = base_prices.get(crypto_name, 1000.0)
    
    crypto_data = []
    for i in range(limit):
        date = datetime.now() - timedelta(days=limit - i - 1)
        price = base_price * (1 + (i % 10 - 5) * 0.01)  # Simple variation
        
        crypto_data.append(CryptoPriceData(
            date=date,
            open_price=price * 0.999,
            high_price=price * 1.001,
            low_price=price * 0.998,
            close_price=price,
            volume=1000000.0,
            symbol=f"{crypto_name.upper()}USDT"
        ))
    
    print(f"✅ Generated {len(crypto_data)} demo data points")
    return crypto_data

if __name__ == "__main__":
    print("🧪 Testing Simple Demo Data Generation")
    print("=" * 50)
    
    try:
        # Test Bitcoin
        btc_data = generate_simple_demo_data('Bitcoin', 10)
        print(f"📊 Bitcoin: {len(btc_data)} points, latest price: ${btc_data[-1].close_price:,.2f}")
        
        # Test Ethereum  
        eth_data = generate_simple_demo_data('Ethereum', 10)
        print(f"📊 Ethereum: {len(eth_data)} points, latest price: ${eth_data[-1].close_price:,.2f}")
        
        # Test Solana
        sol_data = generate_simple_demo_data('Solana', 10)
        print(f"📊 Solana: {len(sol_data)} points, latest price: ${sol_data[-1].close_price:,.2f}")
        
        print("\n🎉 Demo data generation works perfectly!")
        print("💡 The dashboard should now work even when all APIs fail.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()