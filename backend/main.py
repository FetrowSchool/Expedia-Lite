from fastapi import FastAPI
from pydantic import BaseModel

from travel_data import search_stays_by_city

app = FastAPI(title="Expedia Lite API")


class Stay(BaseModel):
    trip_id: str
    trip_name: str
    hotel_name: str
    city: str
    state: str
    check_in: str
    check_out: str
    nights: int
    nightly_rate_usd: float
    stay_price_usd: float


class CitySearchResponse(BaseModel):
    city: str
    stays: list[Stay]


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API is available."""
    return {"status": "ok"}


@app.get("/api/stays", response_model=CitySearchResponse)
def search_stays(city: str) -> CitySearchResponse:
    """Find offered hotel stays by city, ignoring capitalization and outer whitespace."""
    return CitySearchResponse(city=city.strip(), stays=search_stays_by_city(city))
