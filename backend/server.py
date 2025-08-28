from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import math
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class PrayerTimes(BaseModel):
    fajr: str
    sunrise: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str
    date: str
    city: str

class QiblaDirection(BaseModel):
    direction: float
    distance: str
    city: str

class ZakatCalculation(BaseModel):
    cash: float = 0
    savings: float = 0
    gold: float = 0
    silver: float = 0
    business: float = 0
    investments: float = 0
    debts: float = 0

class ZakatResult(BaseModel):
    total_assets: float
    total_debts: float
    net_wealth: float
    nisab_threshold: float
    zakat_due: float
    is_eligible: bool

class CryptoPrice(BaseModel):
    symbol: str
    name: str
    price: float
    change_24h: float
    last_updated: datetime

class WeatherData(BaseModel):
    city: str
    temperature: float
    condition: str
    humidity: float
    wind_speed: float
    last_updated: datetime

class CurrencyRate(BaseModel):
    base: str
    rates: Dict[str, float]
    last_updated: datetime

class IslamicDate(BaseModel):
    hijri_date: str
    gregorian_date: str
    day_name: str

# City coordinates for calculations
CITY_COORDINATES = {
    "Mecca": {"lat": 21.4225, "lng": 39.8262},
    "Medina": {"lat": 24.4686, "lng": 39.6142},
    "New York": {"lat": 40.7128, "lng": -74.0060},
    "London": {"lat": 51.5074, "lng": -0.1278},
    "Dubai": {"lat": 25.2048, "lng": 55.2708},
    "Istanbul": {"lat": 41.0082, "lng": 28.9784},
    "Cairo": {"lat": 30.0444, "lng": 31.2357},
    "Jakarta": {"lat": -6.2088, "lng": 106.8456},
    "Karachi": {"lat": 24.8607, "lng": 67.0011},
    "Riyadh": {"lat": 24.7136, "lng": 46.6753}
}

# Islamic calculation functions
def calculate_qibla_direction(lat1: float, lng1: float) -> Dict[str, Any]:
    """Calculate Qibla direction from given coordinates to Mecca"""
    # Mecca coordinates
    lat2, lng2 = 21.4225, 39.8262
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lng_diff = math.radians(lng2 - lng1)
    
    # Calculate bearing
    y = math.sin(lng_diff) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lng_diff)
    
    bearing = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing) + 360) % 360
    
    # Calculate distance using Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng_diff
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance_km = 6371 * c
    
    return {
        "direction": round(bearing_deg, 1),
        "distance": f"{distance_km:,.0f} km"
    }

def calculate_prayer_times(lat: float, lng: float, date: datetime) -> Dict[str, str]:
    """Calculate prayer times for given location and date"""
    # Simplified prayer time calculation
    # In production, you'd use a proper Islamic prayer time library
    
    # Calculate day of year and solar declination
    day_of_year = date.timetuple().tm_yday
    solar_declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
    # Time corrections based on longitude
    time_correction = (lng - 15 * int(lng / 15)) / 15
    
    # Calculate sunrise and sunset times (simplified)
    lat_rad = math.radians(lat)
    decl_rad = math.radians(solar_declination)
    
    hour_angle = math.degrees(math.acos(-math.tan(lat_rad) * math.tan(decl_rad)))
    
    sunrise_time = 12 - hour_angle / 15 - time_correction
    sunset_time = 12 + hour_angle / 15 - time_correction
    
    # Calculate prayer times based on sunrise/sunset
    fajr_time = sunrise_time - 1.5
    dhuhr_time = 12 - time_correction
    asr_time = dhuhr_time + 4
    maghrib_time = sunset_time + 0.1
    isha_time = maghrib_time + 1.5
    
    def format_time(time_float):
        hours = int(time_float) % 24
        minutes = int((time_float % 1) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    return {
        "fajr": format_time(fajr_time),
        "sunrise": format_time(sunrise_time),
        "dhuhr": format_time(dhuhr_time),
        "asr": format_time(asr_time),
        "maghrib": format_time(maghrib_time),
        "isha": format_time(isha_time)
    }

def calculate_zakat(wealth: ZakatCalculation) -> ZakatResult:
    """Calculate Zakat based on wealth assessment"""
    total_assets = (
        wealth.cash + wealth.savings + wealth.gold + 
        wealth.silver + wealth.business + wealth.investments
    )
    
    net_wealth = total_assets - wealth.debts
    
    # Nisab thresholds (in USD, approximate values)
    gold_nisab = 87.48 * 65  # 87.48 grams * $65/gram
    silver_nisab = 612.36 * 0.8  # 612.36 grams * $0.8/gram
    
    # Use the lower nisab threshold (more favorable to payer)
    nisab_threshold = min(gold_nisab, silver_nisab)
    
    zakat_due = net_wealth * 0.025 if net_wealth >= nisab_threshold else 0
    
    return ZakatResult(
        total_assets=total_assets,
        total_debts=wealth.debts,
        net_wealth=net_wealth,
        nisab_threshold=nisab_threshold,
        zakat_due=zakat_due,
        is_eligible=net_wealth >= nisab_threshold
    )

# Routes
@api_router.get("/")
async def root():
    return {"message": "Zee Tools API - Islamic Utilities Platform"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Prayer Times API
@api_router.get("/prayer-times/{city}", response_model=PrayerTimes)
async def get_prayer_times(city: str):
    """Get prayer times for a specific city"""
    if city not in CITY_COORDINATES:
        raise HTTPException(status_code=404, detail="City not found")
    
    # Check cache first
    today = datetime.now().date()
    cached_times = await db.prayer_times_cache.find_one({
        "city": city,
        "date": today.isoformat()
    })
    
    if cached_times:
        return PrayerTimes(**cached_times)
    
    # Calculate prayer times
    coords = CITY_COORDINATES[city]
    times = calculate_prayer_times(coords["lat"], coords["lng"], datetime.now())
    
    prayer_data = {
        **times,
        "date": today.isoformat(),
        "city": city
    }
    
    # Cache the result
    await db.prayer_times_cache.insert_one({
        **prayer_data,
        "coordinates": coords,
        "created_at": datetime.utcnow()
    })
    
    return PrayerTimes(**prayer_data)

# Qibla Direction API
@api_router.get("/qibla/{city}", response_model=QiblaDirection)
async def get_qibla_direction(city: str):
    """Get Qibla direction for a specific city"""
    if city not in CITY_COORDINATES:
        raise HTTPException(status_code=404, detail="City not found")
    
    coords = CITY_COORDINATES[city]
    qibla_data = calculate_qibla_direction(coords["lat"], coords["lng"])
    
    return QiblaDirection(
        direction=qibla_data["direction"],
        distance=qibla_data["distance"],
        city=city
    )

class CoordinatesInput(BaseModel):
    lat: float
    lng: float

@api_router.post("/qibla/coordinates")
async def get_qibla_by_coordinates(coordinates: CoordinatesInput):
    """Get Qibla direction by coordinates"""
    qibla_data = calculate_qibla_direction(coordinates.lat, coordinates.lng)
    return {
        "direction": qibla_data["direction"],
        "distance": qibla_data["distance"],
        "coordinates": {"lat": coordinates.lat, "lng": coordinates.lng}
    }

# Zakat Calculator API
@api_router.post("/zakat/calculate", response_model=ZakatResult)
async def calculate_zakat_api(wealth: ZakatCalculation):
    """Calculate Zakat based on wealth assessment"""
    return calculate_zakat(wealth)

# Crypto Prices API (using mock data for now)
@api_router.get("/crypto/prices")
async def get_crypto_prices():
    """Get current cryptocurrency prices"""
    # Mock crypto data with some variation
    mock_cryptos = [
        {"symbol": "BTC", "name": "Bitcoin", "price": 45250.30, "change_24h": 2.45},
        {"symbol": "ETH", "name": "Ethereum", "price": 2890.75, "change_24h": -1.23},
        {"symbol": "BNB", "name": "Binance Coin", "price": 315.40, "change_24h": 3.67},
        {"symbol": "ADA", "name": "Cardano", "price": 1.45, "change_24h": 0.85},
        {"symbol": "SOL", "name": "Solana", "price": 98.75, "change_24h": 4.23},
        {"symbol": "DOT", "name": "Polkadot", "price": 23.80, "change_24h": -2.15},
        {"symbol": "MATIC", "name": "Polygon", "price": 0.89, "change_24h": 1.87},
        {"symbol": "AVAX", "name": "Avalanche", "price": 34.60, "change_24h": -0.95},
        {"symbol": "LINK", "name": "Chainlink", "price": 14.25, "change_24h": 2.10},
        {"symbol": "UNI", "name": "Uniswap", "price": 6.75, "change_24h": 1.45},
        {"symbol": "LTC", "name": "Litecoin", "price": 95.30, "change_24h": -1.85},
        {"symbol": "XRP", "name": "Ripple", "price": 0.52, "change_24h": 3.25},
        {"symbol": "ALGO", "name": "Algorand", "price": 0.31, "change_24h": 2.80},
        {"symbol": "VET", "name": "VeChain", "price": 0.023, "change_24h": 1.95},
        {"symbol": "ATOM", "name": "Cosmos", "price": 12.85, "change_24h": -0.65}
    ]
    
    # Add some random variation to simulate live prices
    import random
    for crypto in mock_cryptos:
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        crypto["price"] *= (1 + variation)
        crypto["change_24h"] += random.uniform(-2, 2)
    
    return mock_cryptos

# Weather API
@api_router.get("/weather/{city}")
async def get_weather(city: str):
    """Get weather data for Islamic cities"""
    # Mock weather data
    mock_weather = {
        "Mecca": {"temperature": 32, "condition": "Sunny", "humidity": 45, "wind_speed": 12},
        "Medina": {"temperature": 29, "condition": "Clear", "humidity": 40, "wind_speed": 8},
        "Istanbul": {"temperature": 18, "condition": "Partly Cloudy", "humidity": 65, "wind_speed": 15},
        "Cairo": {"temperature": 25, "condition": "Sunny", "humidity": 35, "wind_speed": 10},
        "Dubai": {"temperature": 35, "condition": "Hot", "humidity": 50, "wind_speed": 20},
        "Jakarta": {"temperature": 28, "condition": "Humid", "humidity": 85, "wind_speed": 5}
    }
    
    if city not in mock_weather:
        raise HTTPException(status_code=404, detail="Weather data not available for this city")
    
    weather = mock_weather[city]
    return WeatherData(
        city=city,
        temperature=weather["temperature"],
        condition=weather["condition"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],
        last_updated=datetime.utcnow()
    )

# Currency Exchange API
@api_router.get("/currency/rates")
async def get_currency_rates():
    """Get current currency exchange rates"""
    # Mock currency rates (base: USD)
    mock_rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "GBP": 0.73,
        "AED": 3.67,
        "SAR": 3.75,
        "PKR": 280.50,
        "INR": 82.75,
        "TRY": 18.90,
        "EGP": 30.85,
        "IDR": 15750
    }
    
    return CurrencyRate(
        base="USD",
        rates=mock_rates,
        last_updated=datetime.utcnow()
    )

# Islamic Calendar API
@api_router.get("/islamic-calendar/today")
async def get_islamic_date_today():
    """Get today's Islamic (Hijri) date"""
    # Simplified Islamic date calculation
    # In production, use proper Hijri calendar library
    
    today = datetime.now()
    
    # Approximate conversion (this is simplified)
    # Islamic calendar started on July 16, 622 CE
    islamic_epoch = datetime(622, 7, 16)
    days_since_epoch = (today - islamic_epoch).days
    
    # Islamic year is approximately 354.37 days
    islamic_year = int(days_since_epoch / 354.37) + 1
    remaining_days = int(days_since_epoch % 354.37)
    
    # Islamic months (approximate days)
    islamic_months = [
        ("Muharram", 30), ("Safar", 29), ("Rabi al-Awwal", 30),
        ("Rabi al-Thani", 29), ("Jumada al-Awwal", 30), ("Jumada al-Thani", 29),
        ("Rajab", 30), ("Sha'ban", 29), ("Ramadan", 30),
        ("Shawwal", 29), ("Dhu al-Qi'dah", 30), ("Dhu al-Hijjah", 29)
    ]
    
    current_month = 1
    current_day = remaining_days
    
    for month_name, month_days in islamic_months:
        if current_day <= month_days:
            break
        current_day -= month_days
        current_month += 1
    
    if current_month > 12:
        current_month = 1
        current_day = 1
    
    hijri_date = f"{current_day} {islamic_months[current_month-1][0]} {islamic_year}"
    
    return IslamicDate(
        hijri_date=hijri_date,
        gregorian_date=today.strftime("%A, %B %d, %Y"),
        day_name=today.strftime("%A")
    )

# Islamic Events API
@api_router.get("/islamic-calendar/events")
async def get_islamic_events():
    """Get Islamic events for 2025"""
    events = [
        {
            "date": "2025-01-29",
            "event": "Rajab Begins",
            "description": "Start of the sacred month of Rajab"
        },
        {
            "date": "2025-02-27",
            "event": "Isra and Mi'raj",
            "description": "Night Journey of Prophet Muhammad (PBUH)"
        },
        {
            "date": "2025-02-28",
            "event": "Sha'ban Begins",
            "description": "Start of the month of Sha'ban"
        },
        {
            "date": "2025-03-14",
            "event": "Laylat al-Bara'ah",
            "description": "Night of Forgiveness (15th Sha'ban)"
        },
        {
            "date": "2025-03-30",
            "event": "Ramadan Begins",
            "description": "Start of the holy month of Ramadan"
        },
        {
            "date": "2025-04-28",
            "event": "Eid al-Fitr",
            "description": "Festival of Breaking the Fast"
        }
    ]
    return events

# Islamic Quotes API
@api_router.get("/islamic-quotes")
async def get_islamic_quotes():
    """Get random Islamic quotes"""
    quotes = [
        "And Allah is the best of planners. - Quran 8:30",
        "So remember Me; I will remember you. - Quran 2:152",
        "And it is He who created the heavens and earth in truth. - Quran 6:73",
        "Allah does not burden a soul beyond that it can bear. - Quran 2:286",
        "And whoever relies upon Allah - then He is sufficient for him. - Quran 65:3",
        "And give good tidings to the patient. - Quran 2:155",
        "So verily, with hardship, there is relief. - Quran 94:5",
        "And Allah loves those who are constantly repentant. - Quran 2:222"
    ]
    
    import random
    return {"quote": random.choice(quotes)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
