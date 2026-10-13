"""Smoke tests for the clinical IBW API contract."""
import pytest
from fastapi import HTTPException
from agents.api import IBWRequest, api_ibw, health


def test_ibw_api_returns_reference_estimates_without_audit_secret():
    response = api_ibw(IBWRequest(sex="M", height_cm=177.8, weight_kg=80))
    assert response["ibw_devine"] == 73.0
    assert response["ibw_robinson"] == 71.0
    assert response["adjusted_bw"] is None
    assert response["patient_id"] == "anonymous"


def test_ibw_api_rejects_unsupported_short_height():
    with pytest.raises(HTTPException) as exc:
        api_ibw(IBWRequest(sex="F", height_cm=145, weight_kg=55))
    assert exc.value.status_code == 422


def test_api_health_is_plain_operational_metadata():
    response = health()
    assert response["status"] == "healthy"
    assert "standard" not in response
