import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
import requests
from sqlalchemy import create_engine, Column, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.schema import PrimaryKeyConstraint

API_KEY = os.getenv("API_KEY", "API_KEY")

router = APIRouter()

SQLITE_DATABASE_URL = "sqlite:///./sqlite.db"

engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SQLiteCityDate(Base):
    __tablename__ = "city_dates"

    city = Column(String(100), index=True, nullable=False)
    date = Column(Date, nullable=False)
    min_temp = Column(Float, default=0.0, nullable=False)
    max_temp = Column(Float, default=0.0, nullable=False)
    avg_temp = Column(Float, default=0.0, nullable=False)
    humidity = Column(Float, default=0.0, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("city", "date", name="city_date_pk"),)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CityDateRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=100, example="New York")
    date: str = Field(..., example="2024-08-06")

    @validator("date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in yyyy-mm-dd format")
        return value


class CityDateResponse(BaseModel):
    city: str
    date: str
    message: str


class CityDateRecordResponse(BaseModel):
    city: str
    date: str
    min_temp: float
    max_temp: float
    avg_temp: float
    humidity: float


def get_data(api_key, city_name, date_input):
    geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city_name, "limit": 1, "appid": api_key}
    response = requests.get(geocoding_url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching city coordinates")

    data = response.json()
    if not data:
        raise HTTPException(
            status_code=404, detail=f"No data found for city {city_name}"
        )

    latitude = data[0]["lat"]
    longitude = data[0]["lon"]

    daily_aggregation_url = (
        "https://api.openweathermap.org/data/3.0/onecall/day_summary"
    )
    params = {
        "lat": latitude,
        "lon": longitude,
        "date": date_input,
        "appid": api_key,
        "units": "metric",
    }
    response = requests.get(daily_aggregation_url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching weather data")

    data = response.json()

    temperature_data = data["temperature"]
    min_temp = temperature_data["min"]
    max_temp = temperature_data["max"]
    avg_temp = (
        temperature_data["afternoon"]
        + temperature_data["night"]
        + temperature_data["evening"]
        + temperature_data["morning"]
    ) / 4
    humidity_data = data["humidity"]
    avg_humidity = humidity_data["afternoon"]

    return max_temp, min_temp, avg_temp, avg_humidity


def create_city_date(
    db: Session, city_name, date_input, max_temp, min_temp, avg_temp, avg_humidity
):
    db_city_date = SQLiteCityDate(
        city=city_name,
        date=datetime.strptime(date_input, "%Y-%m-%d").date(),
        max_temp=max_temp,
        min_temp=min_temp,
        avg_temp=avg_temp,
        humidity=avg_humidity,
    )
    db.add(db_city_date)
    db.commit()
    db.refresh(db_city_date)
    return db_city_date


@router.post("/citydate", response_model=CityDateResponse)
def post_city_date(request: CityDateRequest, db: Session = Depends(get_db)):
    if not request.city:
        raise HTTPException(status_code=400, detail="City name must be provided")

    existing_entry = (
        db.query(SQLiteCityDate)
        .filter(
            SQLiteCityDate.city == request.city,
            SQLiteCityDate.date == datetime.strptime(request.date, "%Y-%m-%d").date(),
        )
        .first()
    )

    if existing_entry:
        raise HTTPException(
            status_code=400, detail="Record already exists for this city and date"
        )

    max_temp, min_temp, avg_temp, avg_humidity = get_data(
        API_KEY, request.city, request.date
    )

    create_city_date(
        db, request.city, request.date, max_temp, min_temp, avg_temp, avg_humidity
    )

    response = CityDateResponse(
        city=request.city,
        date=request.date,
        message=f"Collected data for {request.city} on {request.date}",
    )
    return response


@router.get("/citydate", response_model=list[CityDateRecordResponse])
def get_city_date(
    date: str = Query(..., example="2024-08-06"), db: Session = Depends(get_db)
):
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in yyyy-mm-dd format")

    city_dates = (
        db.query(SQLiteCityDate).filter(SQLiteCityDate.date == query_date).all()
    )

    if not city_dates:
        raise HTTPException(
            status_code=404, detail=f"No records found for the date {date}"
        )

    response = []
    for entry in city_dates:
        response.append(
            CityDateRecordResponse(
                city=entry.city,
                date=entry.date.isoformat(),
                min_temp=entry.min_temp,
                max_temp=entry.max_temp,
                avg_temp=entry.avg_temp,
                humidity=entry.humidity,
            )
        )

    return response
