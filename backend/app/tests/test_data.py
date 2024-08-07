import pytest
from datetime import datetime, timedelta
import requests


@pytest.fixture
def sample_city_data():
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return {"city": "New York", "date": yesterday_date}


def test_post_citydate(base_url, sample_city_data):
    response = requests.post(f"{base_url}/api/v1/data/citydate", json=sample_city_data)
    if response.status_code == 200:
        assert (
            response.json()["message"]
            == f"Received data for {sample_city_data['city']} on {sample_city_data['date']}"
        )
    elif response.status_code == 400:
        assert (
            response.json()["detail"] == "Record already exists for this city and date"
        )
    else:
        pytest.fail(f"Unexpected status code: {response.status_code}")


def test_get_citydate(base_url, sample_city_data):
    response = requests.post(f"{base_url}/api/v1/data/citydate", json=sample_city_data)
    response = requests.get(
        f"{base_url}/api/v1/data/citydate?date={sample_city_data['date']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for record in data:
        assert record["city"] == sample_city_data["city"]
        assert record["date"] == sample_city_data["date"]
        assert isinstance(record["min_temp"], float)
        assert isinstance(record["max_temp"], float)
        assert isinstance(record["avg_temp"], float)
        assert isinstance(record["humidity"], float)
