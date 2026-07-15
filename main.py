#
# [종합실습] 데이터 수집 미니 파이프라인
#
# 작성일 : 2026-07-15
# 작성자 : [김한솔]
#
#
# All Rights Reserved by SK AX, SKALA
#

# main.py
import asyncio
import httpx
import time
import pandas as pd
from typing import Annotated
from pydantic import BaseModel, Field, ValidationError


# 1. Pydantic v2 스키마 정의
class WeatherHourly(BaseModel):
    time: list[str]
    temperature_2m: list[Annotated[float, Field(ge=-40, le=50)]]
    precipitation_probability: list[Annotated[int, Field(ge=0, le=100)]] 

class WeatherData(BaseModel):
    timezone: str
    hourly: WeatherHourly

class CountryData(BaseModel):
    region: str
    population: int = Field(..., ge=0) 

class IpData(BaseModel):
    status: str
    country: str
    city: str


# 2. 비동기 데이터 수집 (asyncio + httpx)
async def fetch_data(client: httpx.AsyncClient, url: str, name: str) -> dict:
    try:
        response = await client.get(url)
        response.raise_for_status() 
        print(f"[정상] {name} 통신 완료")
        return response.json()
    except Exception as e:
        print(f"[오류] {name} 통신 실패: {e}")
        return None

async def collect_all_data():
    urls = {
        "weather": "https://api.open-meteo.com/v1/forecast?latitude=37.55&longitude=127.0&hourly=temperature_2m,precipitation_probability&timezone=Asia%2FSeoul&forecast_days=3",
        "country": "https://countries.dev/alpha/KR", 
        "ip": "http://ip-api.com/json/" 
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(
            fetch_data(client, urls["weather"], "Open-Meteo"),
            fetch_data(client, urls["country"], "RestCountries"),
            fetch_data(client, urls["ip"], "IP-API")
        )
    return results


# 3. 데이터 검증 및 예외 처리
def validate_and_process(weather_json, country_json, ip_json):
    processed_data = []
    
    try:
        weather = WeatherData(**weather_json)
    except ValidationError as e:
        print(f"[날씨 에러] {e}")
        return None
        
    country_region = "Unknown"
    if country_json:
        try:
            country_dict = country_json[0] if isinstance(country_json, list) else country_json
            country = CountryData(**country_dict) 
            country_region = country.region
        except (ValidationError, KeyError):
            print("[예외 처리됨] 국가 API 데이터 형식이 맞지 않아 'Unknown'으로 표기합니다.")
            
    request_city = "Unknown"
    if ip_json:
        try:
            ip = IpData(**ip_json)
            request_city = ip.city
        except ValidationError:
            print("[예외 처리됨] IP API 데이터 오류 - 'Unknown'으로 표기합니다.")
    
    for i in range(len(weather.hourly.time)):
        processed_data.append({
            "time": weather.hourly.time[i],
            "temperature": weather.hourly.temperature_2m[i],
            "precip_prob": weather.hourly.precipitation_probability[i],
            "country_region": country_region,
            "request_city": request_city
        })
        
    print("\n[성공] 데이터 파이프라인 검증 통과! 파일을 생성합니다.")
    return pd.DataFrame(processed_data)


# 4. 성능 비교
def measure_performance(df: pd.DataFrame):
    print("--- [데이터 저장 및 성능 측정 결과] ---")
    
    start_write = time.time()
    df.to_csv("weather_data.csv", index=False)
    csv_write_time = time.time() - start_write
    
    start_read = time.time()
    pd.read_csv("weather_data.csv")
    csv_read_time = time.time() - start_read
    
    print(f"CSV     | 쓰기: {csv_write_time:.5f}초 | 읽기: {csv_read_time:.5f}초")

    start_write = time.time()
    df.to_parquet("weather_data.parquet", engine="pyarrow")
    parquet_write_time = time.time() - start_write
    
    start_read = time.time()
    pd.read_parquet("weather_data.parquet", engine="pyarrow")
    parquet_read_time = time.time() - start_read
    
    print(f"Parquet | 쓰기: {parquet_write_time:.5f}초 | 읽기: {parquet_read_time:.5f}초")

if __name__ == "__main__":
    print("비동기 API 파이프라인 시작...\n")
    results = asyncio.run(collect_all_data())
    weather_json, country_json, ip_json = results
    
    if weather_json:
        df = validate_and_process(weather_json, country_json, ip_json)
        if df is not None:
            measure_performance(df)