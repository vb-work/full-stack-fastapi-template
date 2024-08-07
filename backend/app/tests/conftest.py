import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--url", action="store", default="http://localhost", help="Base URL for the API"
    )


@pytest.fixture
def base_url(request):
    return request.config.getoption("--url")
