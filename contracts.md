# Zee Tools - Backend Integration Contracts

## API Contracts Overview

### Base URL: `/api`
All backend endpoints will be prefixed with `/api` to match Kubernetes ingress rules.

## Data Integration Plan

### 1. Prayer Times API
**Endpoint:** `GET /api/prayer-times/:city`
**Mock Data to Replace:** `mockPrayerTimes` in mock/data.js
**Integration:** Replace hardcoded times with calculated prayer times based on city coordinates
**Frontend Integration:** Update PrayerTimes.jsx to use actual API

### 2. Qibla Direction API  
**Endpoint:** `GET /api/qibla/:city` or `POST /api/qibla` (with coordinates)
**Mock Data to Replace:** `mockQiblaDirection` in mock/data.js
**Integration:** Calculate actual Qibla direction using coordinates and Mecca location
**Frontend Integration:** Update QiblaFinder.jsx to use real calculations

### 3. Cryptocurrency Tracking
**Endpoint:** `GET /api/crypto/prices`
**Mock Data to Replace:** `mockCryptoData` in mock/data.js
**Integration:** Fetch live crypto prices from public APIs (CoinGecko/CoinMarketCap)
**Frontend Integration:** Update CryptoTracker.jsx with real-time data

### 4. Weather Data
**Endpoint:** `GET /api/weather/:city`
**Mock Data to Replace:** `mockWeatherData` in mock/data.js
**Integration:** Fetch weather from public weather APIs
**Frontend Integration:** Update WeatherTool.jsx with actual weather

### 5. Currency Exchange
**Endpoint:** `GET /api/currency/rates`
**Mock Data to Replace:** `mockCurrencyRates` in mock/data.js
**Integration:** Fetch live exchange rates from currency APIs
**Frontend Integration:** Update CurrencyExchange.jsx with real rates

### 6. Islamic Calendar & Events
**Endpoint:** `GET /api/islamic-calendar`
**Mock Data to Replace:** `mockIslamicEvents` in mock/data.js
**Integration:** Calculate Islamic dates and store events in database
**Frontend Integration:** Update IslamicCalendar.jsx with calculated dates

### 7. Zakat Calculator
**Endpoint:** `POST /api/zakat/calculate`
**Body:** `{ wealth: {...}, location?: string }`
**Integration:** Server-side Zakat calculations with current gold/silver prices
**Frontend Integration:** Update ZakatCalculator.jsx to use API calculations

## Database Models

### 1. Prayer Times Cache
```javascript
{
  city: String,
  coordinates: { lat: Number, lng: Number },
  prayerTimes: {
    fajr: String,
    sunrise: String,
    dhuhr: String,
    asr: String,
    maghrib: String,
    isha: String
  },
  date: Date,
  createdAt: Date
}
```

### 2. Islamic Events
```javascript
{
  event: String,
  description: String,
  hijriDate: String,
  gregorianDate: Date,
  year: Number,
  isRecurring: Boolean
}
```

### 3. User Preferences (Optional)
```javascript
{
  sessionId: String,
  favoriteCity: String,
  cryptoFavorites: [String],
  calculationSettings: Object,
  createdAt: Date
}
```

## Implementation Priority

### Phase 1: Core Islamic Features
1. Prayer Times calculation and caching
2. Qibla direction calculation
3. Zakat calculator with live gold/silver prices
4. Islamic calendar date conversion

### Phase 2: Financial Tools
1. Cryptocurrency price fetching
2. Currency exchange rates
3. Weather data integration

### Phase 3: Enhancements
1. User preferences storage
2. Caching strategies
3. Rate limiting
4. Error handling improvements

## Frontend Integration Points

### Mock Data Replacement Strategy
1. Keep mock data as fallback
2. Update API calls to use `${BACKEND_URL}/api/...`
3. Add loading states
4. Add error handling with fallback to mock data

### API Call Pattern
```javascript
const fetchPrayerTimes = async (city) => {
  try {
    const response = await axios.get(`${API}/prayer-times/${city}`);
    return response.data;
  } catch (error) {
    console.warn('API failed, using mock data:', error);
    return mockPrayerTimes[city] || mockPrayerTimes['Mecca'];
  }
};
```

## External APIs to Integrate

1. **Prayer Times:** Custom calculation using coordinates and Islamic formulas
2. **Crypto Prices:** CoinGecko Free API or similar
3. **Weather:** OpenWeatherMap or similar free API
4. **Currency:** Fixer.io, ExchangeRate-API, or similar
5. **Gold/Silver Prices:** Financial data APIs

## Error Handling Strategy

1. Always provide fallback to mock data
2. Cache successful API responses
3. Graceful degradation for network issues
4. User-friendly error messages

## Performance Optimizations

1. Cache prayer times for 24 hours
2. Cache crypto prices for 1-5 minutes
3. Cache weather data for 30 minutes
4. Cache currency rates for 1 hour
5. Use MongoDB TTL indexes for automatic cleanup