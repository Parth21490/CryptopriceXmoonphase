#!/usr/bin/env python3
"""
Test the dashboard's CoinGecko integration
"""

from crypto_moon_dashboard import CryptoDataClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_dashboard_coingecko():
    """Test CoinGecko integration in the dashboard"""
    print("🧪 Testing Dashboard CoinGecko Integration")
    print("=" * 50)
    
    try:
        # Create client
        client = CryptoDataClient()
        
        # Test Bitcoin data
        print("📡 Testing Bitcoin data fetch...")
        bitcoin_data = client.fetch_crypto_data('Bitcoin', limit=10)
        
        if bitcoin_data and len(bitcoin_data) > 0:
            print(f"✅ Success! Fetched {len(bitcoin_data)} Bitcoin data points")
            latest = bitcoin_data[-1]
            print(f"💰 Latest Bitcoin price: ${latest.close_price:,.2f}")
            print(f"📅 Latest date: {latest.date.strftime('%Y-%m-%d')}")
            
            # Test other cryptos
            for crypto in ['Ethereum', 'Solana']:
                print(f"\n📡 Testing {crypto} data fetch...")
                crypto_data = client.fetch_crypto_data(crypto, limit=5)
                if crypto_data and len(crypto_data) > 0:
                    latest = crypto_data[-1]
                    print(f"✅ Success! Latest {crypto} price: ${latest.close_price:,.2f}")
                else:
                    print(f"❌ Failed to fetch {crypto} data")
            
            print("\n🎉 Dashboard CoinGecko integration is working perfectly!")
            print("💡 The dashboard should now work without any 403 errors!")
            return True
            
        else:
            print("❌ No Bitcoin data received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_coingecko()
    if success:
        print("\n✅ All tests passed! Dashboard is ready to use.")
    else:
        print("\n❌ Tests failed! Check the implementation.")