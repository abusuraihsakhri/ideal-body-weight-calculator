"""Regression coverage for input safety, CSV units, and audit integrity."""
import csv
import math
import secrets
import tempfile
from pathlib import Path

import pytest

import ibw
from agents.base import AuditTrail


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_height_does_not_produce_estimates(invalid):
    result = ibw.calculate_patient("anon", "M", invalid, 80)
    assert result.ibw_devine is None
    assert any("finite" in warning for warning in result.warnings)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_weight_does_not_produce_estimates(invalid):
    result = ibw.calculate_patient("anon", "M", 175, invalid)
    assert result.ibw_devine is None
    assert any("finite" in warning for warning in result.warnings)


def test_height_below_formula_threshold_does_not_extrapolate():
    result = ibw.calculate_patient("anon", "F", 150, 80)
    assert result.ibw_devine is None
    assert result.percent_ibw is None
    assert any("below the minimum" in warning for warning in result.warnings)


def test_invalid_csv_weight_unit_does_not_become_kg():
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "input.csv"
        destination = Path(folder) / "output.csv"
        source.write_text("patient_id,sex,height_cm,weight_kg,weight_unit\nA,M,175,80,stone\n")
        results = ibw.process_csv(str(source), str(destination))
        assert results[0].ibw_devine is None
        assert "Unsupported weight unit" in results[0].warnings[0]
        with destination.open(newline="") as file:
            assert "Unsupported weight unit" in list(csv.DictReader(file))[0]["warnings"]


def test_audit_detects_modified_signed_fields_and_chain_links():
    trail = AuditTrail(secret_key=secrets.token_hex(32))
    trail.log("tester", "unit", "CREATE", {"status": "ok"})
    trail.log("tester", "unit", "UPDATE", {"status": "ok"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "mutated-snapshot"
    assert trail.verify_integrity()  # Snapshot must not mutate internal state.
    trail.logs[0]["actor"] = "tampered"
    assert not trail.verify_integrity()
    trail.logs[0]["actor"] = "tester"
    assert trail.verify_integrity()
    trail.logs[1]["prev_hash"] = "forged"
    assert not trail.verify_integrity()


def test_invalid_cli_single_exits_nonzero():
    assert ibw.main(["single", "--sex", "M", "--height", "150", "--weight", "80"]) == 2


def test_csv_spreadsheet_formula_is_escaped():
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "input.csv"
        destination = Path(folder) / "output.csv"
        source.write_text("patient_id,sex,height_cm,weight_kg\n=1+2,M,175,80\n")
        ibw.process_csv(str(source), str(destination))
        with destination.open(newline="") as file:
            exported = list(csv.DictReader(file))
        assert exported[0]["patient_id"] == "'=1+2"
