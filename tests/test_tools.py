"""
Unit and API Integration Tests for AI Tools Registry and Capabilities
(DGAI-M4-SPEC v6.0.0 Article 0.1 & M4a)
"""

import pytest
import json
from main import app
from dgai.tools import (
    get_current_time,
    calculator,
    get_system_info,
    weather_lookup,
    memory_store,
    memory_retrieve,
    execute_tool_call,
    TOOL_SCHEMAS
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_time_and_calc_tools():
    time_res = get_current_time()
    assert "time" in time_res
    assert "date" in time_res

    calc_res = calculator("10 + 2 * 5")
    assert calc_res["status"] == "success"
    assert calc_res["result"] == 20


def test_system_and_weather_tools():
    sys_res = get_system_info()
    assert "python_version" in sys_res

    weather_res = weather_lookup("Paris")
    assert weather_res["location"] == "Paris"
    assert "temperature_celsius" in weather_res


def test_memory_store_and_retrieve():
    store_res = memory_store("user_preference_theme", "dark")
    assert store_res["status"] == "stored"

    ret_res = memory_retrieve("user_preference_theme")
    assert ret_res["status"] == "found"
    assert ret_res["value"] == "dark"


def test_tools_list_api_endpoint(client):
    rv = client.get('/api/v1/tools')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["count"] == len(TOOL_SCHEMAS)


def test_tool_execute_time_and_calc_api_endpoints(client):
    # Execute time
    rv_time = client.post('/api/v1/tools/execute', json={
        "name": "get_current_time",
        "arguments": {"timezone": "UTC"}
    })
    assert rv_time.status_code == 200
    data_time = json.loads(rv_time.data)
    assert "time" in data_time["result"]

    # Execute calc
    rv_calc = client.post('/api/v1/tools/execute', json={
        "name": "calculator",
        "arguments": {"expression": "pow(2, 8)"}
    })
    assert rv_calc.status_code == 200
    data_calc = json.loads(rv_calc.data)
    assert data_calc["result"]["result"] == 256
