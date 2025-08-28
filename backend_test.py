#!/usr/bin/env python3
"""
Islamic Tools Backend API Test Suite
Tests all backend endpoints for the Islamic utilities platform
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://islamic-utilities.preview.emergentagent.com/api"

class IslamicToolsAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        
        self.test_results.append(result)
        if not success:
            self.failed_tests.append(test_name)
        print(result)
        
    def test_root_endpoint(self):
        """Test GET /api/ - Root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Islamic" in data["message"]:
                    self.log_test("Root Endpoint", True, f"Message: {data['message']}")
                else:
                    self.log_test("Root Endpoint", False, f"Unexpected response format: {data}")
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
    
    def test_prayer_times(self):
        """Test GET /api/prayer-times/{city} - Prayer times for cities"""
        test_cities = ["Mecca", "New York", "London", "Dubai", "Istanbul"]
        
        for city in test_cities:
            try:
                response = requests.get(f"{self.base_url}/prayer-times/{city}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha", "date", "city"]
                    
                    if all(field in data for field in required_fields):
                        # Validate time format (HH:MM)
                        time_valid = True
                        for time_field in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
                            time_str = data[time_field]
                            if not (len(time_str) == 5 and time_str[2] == ':'):
                                time_valid = False
                                break
                        
                        if time_valid and data["city"] == city:
                            self.log_test(f"Prayer Times - {city}", True, f"Date: {data['date']}")
                        else:
                            self.log_test(f"Prayer Times - {city}", False, "Invalid time format or city mismatch")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test(f"Prayer Times - {city}", False, f"Missing fields: {missing}")
                else:
                    self.log_test(f"Prayer Times - {city}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Prayer Times - {city}", False, f"Exception: {str(e)}")
        
        # Test invalid city
        try:
            response = requests.get(f"{self.base_url}/prayer-times/InvalidCity", timeout=10)
            if response.status_code == 404:
                self.log_test("Prayer Times - Invalid City", True, "Correctly returned 404")
            else:
                self.log_test("Prayer Times - Invalid City", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Prayer Times - Invalid City", False, f"Exception: {str(e)}")
    
    def test_qibla_direction(self):
        """Test GET /api/qibla/{city} - Qibla direction for cities"""
        test_cities = ["Mecca", "New York", "London", "Dubai", "Jakarta"]
        
        for city in test_cities:
            try:
                response = requests.get(f"{self.base_url}/qibla/{city}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["direction", "distance", "city"]
                    
                    if all(field in data for field in required_fields):
                        direction = data["direction"]
                        distance = data["distance"]
                        
                        # Validate direction is between 0-360
                        if 0 <= direction <= 360 and "km" in distance and data["city"] == city:
                            # Special case: Mecca should have direction 0 and minimal distance
                            if city == "Mecca":
                                if direction < 10 and "0 km" in distance:
                                    self.log_test(f"Qibla Direction - {city}", True, f"Direction: {direction}°, Distance: {distance}")
                                else:
                                    self.log_test(f"Qibla Direction - {city}", False, f"Mecca should have ~0° direction and minimal distance")
                            else:
                                self.log_test(f"Qibla Direction - {city}", True, f"Direction: {direction}°, Distance: {distance}")
                        else:
                            self.log_test(f"Qibla Direction - {city}", False, f"Invalid direction ({direction}) or distance format")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test(f"Qibla Direction - {city}", False, f"Missing fields: {missing}")
                else:
                    self.log_test(f"Qibla Direction - {city}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Qibla Direction - {city}", False, f"Exception: {str(e)}")
    
    def test_qibla_coordinates(self):
        """Test POST /api/qibla/coordinates - Qibla direction by coordinates"""
        test_coordinates = [
            {"lat": 40.7128, "lng": -74.0060, "name": "New York"},
            {"lat": 51.5074, "lng": -0.1278, "name": "London"},
            {"lat": 25.2048, "lng": 55.2708, "name": "Dubai"}
        ]
        
        for coord in test_coordinates:
            try:
                payload = {"lat": coord["lat"], "lng": coord["lng"]}
                response = requests.post(f"{self.base_url}/qibla/coordinates", 
                                       json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["direction", "distance", "coordinates"]
                    
                    if all(field in data for field in required_fields):
                        direction = data["direction"]
                        distance = data["distance"]
                        coords = data["coordinates"]
                        
                        # Validate response
                        if (0 <= direction <= 360 and "km" in distance and 
                            coords["lat"] == coord["lat"] and coords["lng"] == coord["lng"]):
                            self.log_test(f"Qibla Coordinates - {coord['name']}", True, 
                                        f"Direction: {direction}°, Distance: {distance}")
                        else:
                            self.log_test(f"Qibla Coordinates - {coord['name']}", False, 
                                        "Invalid direction, distance, or coordinates")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test(f"Qibla Coordinates - {coord['name']}", False, f"Missing fields: {missing}")
                else:
                    self.log_test(f"Qibla Coordinates - {coord['name']}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Qibla Coordinates - {coord['name']}", False, f"Exception: {str(e)}")
    
    def test_zakat_calculation(self):
        """Test POST /api/zakat/calculate - Zakat calculation"""
        test_cases = [
            {
                "name": "High Wealth",
                "data": {
                    "cash": 10000,
                    "savings": 20000,
                    "gold": 5000,
                    "silver": 2000,
                    "business": 15000,
                    "investments": 8000,
                    "debts": 3000
                }
            },
            {
                "name": "Low Wealth",
                "data": {
                    "cash": 500,
                    "savings": 300,
                    "gold": 0,
                    "silver": 0,
                    "business": 0,
                    "investments": 0,
                    "debts": 100
                }
            },
            {
                "name": "Zero Wealth",
                "data": {
                    "cash": 0,
                    "savings": 0,
                    "gold": 0,
                    "silver": 0,
                    "business": 0,
                    "investments": 0,
                    "debts": 0
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                response = requests.post(f"{self.base_url}/zakat/calculate", 
                                       json=test_case["data"], timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["total_assets", "total_debts", "net_wealth", 
                                     "nisab_threshold", "zakat_due", "is_eligible"]
                    
                    if all(field in data for field in required_fields):
                        # Validate calculations
                        expected_assets = sum([
                            test_case["data"]["cash"], test_case["data"]["savings"],
                            test_case["data"]["gold"], test_case["data"]["silver"],
                            test_case["data"]["business"], test_case["data"]["investments"]
                        ])
                        expected_net = expected_assets - test_case["data"]["debts"]
                        
                        if (abs(data["total_assets"] - expected_assets) < 0.01 and
                            abs(data["net_wealth"] - expected_net) < 0.01 and
                            data["total_debts"] == test_case["data"]["debts"]):
                            
                            # Check zakat calculation logic
                            if data["is_eligible"]:
                                expected_zakat = data["net_wealth"] * 0.025
                                if abs(data["zakat_due"] - expected_zakat) < 0.01:
                                    self.log_test(f"Zakat Calculation - {test_case['name']}", True, 
                                                f"Zakat Due: ${data['zakat_due']:.2f}")
                                else:
                                    self.log_test(f"Zakat Calculation - {test_case['name']}", False, 
                                                "Incorrect zakat calculation")
                            else:
                                if data["zakat_due"] == 0:
                                    self.log_test(f"Zakat Calculation - {test_case['name']}", True, 
                                                "Not eligible for zakat")
                                else:
                                    self.log_test(f"Zakat Calculation - {test_case['name']}", False, 
                                                "Should have zero zakat when not eligible")
                        else:
                            self.log_test(f"Zakat Calculation - {test_case['name']}", False, 
                                        "Incorrect asset or debt calculations")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test(f"Zakat Calculation - {test_case['name']}", False, f"Missing fields: {missing}")
                else:
                    self.log_test(f"Zakat Calculation - {test_case['name']}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Zakat Calculation - {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_crypto_prices(self):
        """Test GET /api/crypto/prices - Cryptocurrency prices"""
        try:
            response = requests.get(f"{self.base_url}/crypto/prices", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Check first crypto entry
                    crypto = data[0]
                    required_fields = ["symbol", "name", "price", "change_24h"]
                    
                    if all(field in crypto for field in required_fields):
                        # Validate data types and reasonable values
                        if (isinstance(crypto["price"], (int, float)) and crypto["price"] > 0 and
                            isinstance(crypto["change_24h"], (int, float)) and
                            isinstance(crypto["symbol"], str) and isinstance(crypto["name"], str)):
                            self.log_test("Crypto Prices", True, f"Found {len(data)} cryptocurrencies")
                        else:
                            self.log_test("Crypto Prices", False, "Invalid data types or values")
                    else:
                        missing = [f for f in required_fields if f not in crypto]
                        self.log_test("Crypto Prices", False, f"Missing fields in crypto data: {missing}")
                else:
                    self.log_test("Crypto Prices", False, "Empty or invalid response format")
            else:
                self.log_test("Crypto Prices", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Crypto Prices", False, f"Exception: {str(e)}")
    
    def test_weather(self):
        """Test GET /api/weather/{city} - Weather for Islamic cities"""
        test_cities = ["Mecca", "Medina", "Istanbul", "Cairo", "Dubai", "Jakarta"]
        
        for city in test_cities:
            try:
                response = requests.get(f"{self.base_url}/weather/{city}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["city", "temperature", "condition", "humidity", "wind_speed", "last_updated"]
                    
                    if all(field in data for field in required_fields):
                        # Validate data types and reasonable values
                        if (data["city"] == city and
                            isinstance(data["temperature"], (int, float)) and -50 <= data["temperature"] <= 60 and
                            isinstance(data["humidity"], (int, float)) and 0 <= data["humidity"] <= 100 and
                            isinstance(data["wind_speed"], (int, float)) and data["wind_speed"] >= 0 and
                            isinstance(data["condition"], str)):
                            self.log_test(f"Weather - {city}", True, 
                                        f"{data['temperature']}°C, {data['condition']}")
                        else:
                            self.log_test(f"Weather - {city}", False, "Invalid data values or types")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_test(f"Weather - {city}", False, f"Missing fields: {missing}")
                else:
                    self.log_test(f"Weather - {city}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Weather - {city}", False, f"Exception: {str(e)}")
        
        # Test invalid city
        try:
            response = requests.get(f"{self.base_url}/weather/InvalidCity", timeout=10)
            if response.status_code == 404:
                self.log_test("Weather - Invalid City", True, "Correctly returned 404")
            else:
                self.log_test("Weather - Invalid City", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Weather - Invalid City", False, f"Exception: {str(e)}")
    
    def test_currency_rates(self):
        """Test GET /api/currency/rates - Currency exchange rates"""
        try:
            response = requests.get(f"{self.base_url}/currency/rates", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["base", "rates", "last_updated"]
                
                if all(field in data for field in required_fields):
                    # Validate base currency and rates
                    if (data["base"] == "USD" and isinstance(data["rates"], dict) and
                        len(data["rates"]) > 0):
                        
                        # Check some expected currencies
                        expected_currencies = ["USD", "EUR", "GBP", "AED", "SAR"]
                        found_currencies = [curr for curr in expected_currencies if curr in data["rates"]]
                        
                        if len(found_currencies) >= 3:
                            # Validate rate values
                            valid_rates = all(isinstance(rate, (int, float)) and rate > 0 
                                            for rate in data["rates"].values())
                            if valid_rates:
                                self.log_test("Currency Rates", True, 
                                            f"Base: {data['base']}, {len(data['rates'])} currencies")
                            else:
                                self.log_test("Currency Rates", False, "Invalid rate values")
                        else:
                            self.log_test("Currency Rates", False, f"Missing expected currencies")
                    else:
                        self.log_test("Currency Rates", False, "Invalid base currency or rates format")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Currency Rates", False, f"Missing fields: {missing}")
            else:
                self.log_test("Currency Rates", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Currency Rates", False, f"Exception: {str(e)}")
    
    def test_islamic_calendar_today(self):
        """Test GET /api/islamic-calendar/today - Today's Islamic date"""
        try:
            response = requests.get(f"{self.base_url}/islamic-calendar/today", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["hijri_date", "gregorian_date", "day_name"]
                
                if all(field in data for field in required_fields):
                    # Validate date formats
                    hijri = data["hijri_date"]
                    gregorian = data["gregorian_date"]
                    day_name = data["day_name"]
                    
                    # Basic validation - hijri should contain Islamic month names
                    islamic_months = ["Muharram", "Safar", "Rabi", "Jumada", "Rajab", "Sha'ban", 
                                    "Ramadan", "Shawwal", "Dhu"]
                    
                    has_islamic_month = any(month in hijri for month in islamic_months)
                    has_valid_day = any(day in day_name for day in ["Monday", "Tuesday", "Wednesday", 
                                                                   "Thursday", "Friday", "Saturday", "Sunday"])
                    
                    if has_islamic_month and has_valid_day and len(gregorian) > 10:
                        self.log_test("Islamic Calendar Today", True, f"Hijri: {hijri}")
                    else:
                        self.log_test("Islamic Calendar Today", False, "Invalid date format")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Islamic Calendar Today", False, f"Missing fields: {missing}")
            else:
                self.log_test("Islamic Calendar Today", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Islamic Calendar Today", False, f"Exception: {str(e)}")
    
    def test_islamic_events(self):
        """Test GET /api/islamic-calendar/events - Islamic events for 2025"""
        try:
            response = requests.get(f"{self.base_url}/islamic-calendar/events", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    # Check first event
                    event = data[0]
                    required_fields = ["date", "event", "description"]
                    
                    if all(field in event for field in required_fields):
                        # Validate date format (YYYY-MM-DD)
                        date_str = event["date"]
                        if (len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-' and
                            date_str.startswith("2025")):
                            
                            # Check for Islamic events
                            islamic_events = ["Ramadan", "Eid", "Rajab", "Isra", "Mi'raj", "Sha'ban"]
                            has_islamic_event = any(ie in event["event"] or ie in event["description"] 
                                                  for ie in islamic_events)
                            
                            if has_islamic_event:
                                self.log_test("Islamic Events", True, f"Found {len(data)} events for 2025")
                            else:
                                self.log_test("Islamic Events", False, "No recognizable Islamic events found")
                        else:
                            self.log_test("Islamic Events", False, "Invalid date format")
                    else:
                        missing = [f for f in required_fields if f not in event]
                        self.log_test("Islamic Events", False, f"Missing fields in event: {missing}")
                else:
                    self.log_test("Islamic Events", False, "Empty or invalid response format")
            else:
                self.log_test("Islamic Events", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Islamic Events", False, f"Exception: {str(e)}")
    
    def test_islamic_quotes(self):
        """Test GET /api/islamic-quotes - Random Islamic quotes"""
        try:
            response = requests.get(f"{self.base_url}/islamic-quotes", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "quote" in data and isinstance(data["quote"], str) and len(data["quote"]) > 10:
                    # Check if it contains Islamic references
                    islamic_terms = ["Allah", "Quran", "Prophet", "Muhammad", "PBUH"]
                    has_islamic_content = any(term in data["quote"] for term in islamic_terms)
                    
                    if has_islamic_content:
                        self.log_test("Islamic Quotes", True, f"Quote length: {len(data['quote'])} chars")
                    else:
                        self.log_test("Islamic Quotes", False, "Quote doesn't contain Islamic references")
                else:
                    self.log_test("Islamic Quotes", False, "Invalid quote format or missing quote field")
            else:
                self.log_test("Islamic Quotes", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Islamic Quotes", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Islamic Tools API Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        self.test_root_endpoint()
        self.test_prayer_times()
        self.test_qibla_direction()
        self.test_qibla_coordinates()
        self.test_zakat_calculation()
        self.test_crypto_prices()
        self.test_weather()
        self.test_currency_rates()
        self.test_islamic_calendar_today()
        self.test_islamic_events()
        self.test_islamic_quotes()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        failed_count = len(self.failed_tests)
        passed_count = total_tests - failed_count
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_count}")
        print(f"❌ Failed: {failed_count}")
        
        if self.failed_tests:
            print(f"\n🔍 Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return failed_count == 0

if __name__ == "__main__":
    tester = IslamicToolsAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Islamic Tools API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Please check the backend implementation.")
        sys.exit(1)