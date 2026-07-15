import pytest
from pydantic import ValidationError
from main import WeatherHourly, CountryData, IpData


def test_weather_hourly_valid():
    hourly = WeatherHourly(
        time=["2026-07-15T00:00"],
        temperature_2m=[25.0],
        precipitation_probability=[50],
    )
    assert hourly.temperature_2m == [25.0]


def test_weather_hourly_temperature_out_of_range_raises():
    with pytest.raises(ValidationError):
        WeatherHourly(
            time=["2026-07-15T00:00"],
            temperature_2m=[100.0],
            precipitation_probability=[50],
        )


def test_weather_hourly_precipitation_out_of_range_raises():
    with pytest.raises(ValidationError):
        WeatherHourly(
            time=["2026-07-15T00:00"],
            temperature_2m=[25.0],
            precipitation_probability=[150],
        )


def test_country_data_valid():
    country = CountryData(region="Asia", population=51000000)
    assert country.region == "Asia"


def test_country_data_negative_population_raises():
    with pytest.raises(ValidationError):
        CountryData(region="Asia", population=-1)


def test_ip_data_valid():
    ip = IpData(status="success", country="South Korea", city="Seoul")
    assert ip.city == "Seoul"
