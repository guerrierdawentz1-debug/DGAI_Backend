"""
Unit and API Integration Tests for Native DGAI AI Tools
(DGAI-M4-SPEC v6.0.0 Section 0.1 & Article 3)
"""

import pytest
import json
from main import app
from dgai.tools import get_current_time, calculator, get_system_info, manage_context_memory, execute_tool_call


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_time_and_calc_tools():
    # Time tool
    time_res = get_current_time()
    assert time_res["timezone"] == "UTC"
    assert "date" in time_res

    # Calculator tool
    calc_res = calculator("15 * 12 + sqrt(144)")
    assert calc_res["status"] == "success"
    assert calc_res["result"] == 192.0

    # System info tool
    sys_res = get_system_info()
    assert sys_res["spec_version"] == "DGAI-M4-SPEC v6.0.0"


def test_context_memory_tool():
    res_set = manage_context_memory("set", key="user_name", value="Alexandre")
    assert res_set["status"] == "success"

    res_get = manage_context_memory("get", key="user_name")
    assert res_get["value"] == "Alexandre"


def test_tool_execute_time_and_calc_api_endpoints(client):
    rv_time = client.post('/api/v1/tools/execute', json={
        "name": "get_current_time",
        "arguments": {}
    })
    assert rv_time.status_code == 200
    data_time = json.loads(rv_time.data)
    assert data_time["result"]["timezone"] == "UTC"

    rv_calc = client.post('/api/v1/tools/execute', json={
        "name": "calculator",
        "arguments": {"expression": "2 ** 10"}
    })
    assert rv_calc.status_code == 200
    data_calc = json.loads(rv_calc.data)
    assert data_calc["result"]["result"] == 1024
