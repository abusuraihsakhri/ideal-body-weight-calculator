"""Tests for ibw.py -- plain assert statements, stdlib only.

Run with: python test_ibw.py
"""

import csv
import math
import os
import tempfile

import ibw


# ---------------------------------------------------------------------------
# Devine formula
# ---------------------------------------------------------------------------

def test_devine_male_5ft10():
    """5'10\" = 70 inches: 50 + 2.3*(70-60) = 50 + 23 = 73 kg."""
    result = ibw.ibw_devine(70, "M")
    assert math.isclose(result, 73.0, abs_tol=0.01), result


def test_devine_female_5ft4():
    """5'4\" = 64 inches: 45.5 + 2.3*(64-60) = 45.5 + 9.2 = 54.7 kg."""
    result = ibw.ibw_devine(64, "F")
    assert math.isclose(result, 54.7, abs_tol=0.01), result


def test_devine_male_6ft():
    """6'0\" = 72 inches: 50 + 2.3*(72-60) = 50 + 27.6 = 77.6 kg."""
    result = ibw.ibw_devine(72, "M")
    assert math.isclose(result, 77.6, abs_tol=0.01), result


def test_devine_female_5ft():
    """5'0\" = 60 inches: 45.5 + 2.3*(60-60) = 45.5 kg."""
    result = ibw.ibw_devine(60, "F")
    assert math.isclose(result, 45.5, abs_tol=0.01), result


def test_devine_invalid_sex():
    try:
        ibw.ibw_devine(70, "X")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Robinson formula
# ---------------------------------------------------------------------------

def test_robinson_male():
    """70 inches: 52 + 1.9*(70-60) = 52 + 19 = 71 kg."""
    result = ibw.ibw_robinson(70, "M")
    assert math.isclose(result, 71.0, abs_tol=0.01), result


def test_robinson_female():
    """64 inches: 49 + 1.7*(64-60) = 49 + 6.8 = 55.8 kg."""
    result = ibw.ibw_robinson(64, "F")
    assert math.isclose(result, 55.8, abs_tol=0.01), result


# ---------------------------------------------------------------------------
# Miller formula
# ---------------------------------------------------------------------------

def test_miller_male():
    """70 inches: 56.2 + 1.41*(70-60) = 56.2 + 14.1 = 70.3 kg."""
    result = ibw.ibw_miller(70, "M")
    assert math.isclose(result, 70.3, abs_tol=0.01), result


def test_miller_female():
    """64 inches: 53.1 + 1.36*(64-60) = 53.1 + 5.44 = 58.54 kg."""
    result = ibw.ibw_miller(64, "F")
    assert math.isclose(result, 58.54, abs_tol=0.01), result


# ---------------------------------------------------------------------------
# Hamwi formula
# ---------------------------------------------------------------------------

def test_hamwi_male():
    """70 inches: 48 + 2.7*(70-60) = 48 + 27 = 75 kg."""
    result = ibw.ibw_hamwi(70, "M")
    assert math.isclose(result, 75.0, abs_tol=0.01), result


def test_hamwi_female():
    """64 inches: 45.5 + 2.2*(64-60) = 45.5 + 8.8 = 54.3 kg."""
    result = ibw.ibw_hamwi(64, "F")
    assert math.isclose(result, 54.3, abs_tol=0.01), result


# ---------------------------------------------------------------------------
# Adjusted Body Weight
# ---------------------------------------------------------------------------

def test_adjusted_bw():
    """AjBW = IBW + 0.4*(actual - IBW) = 70 + 0.4*(100-70) = 70 + 12 = 82."""
    result = ibw.adjusted_body_weight(100, 70)
    assert math.isclose(result, 82.0, abs_tol=0.01), result


def test_adjusted_bw_no_excess():
    """When actual == IBW, AjBW = IBW."""
    result = ibw.adjusted_body_weight(70, 70)
    assert math.isclose(result, 70.0, abs_tol=0.01), result


def test_percent_ibw():
    """100kg / 70kg IBW = 142.86%."""
    result = ibw.percent_ibw(100, 70)
    assert math.isclose(result, 142.86, abs_tol=0.1), result


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

def test_height_to_inches():
    """177.8 cm = 70 inches."""
    result = ibw.height_to_inches(177.8)
    assert math.isclose(result, 70.0, abs_tol=0.1), result


def test_weight_to_kg():
    """154 lbs ≈ 69.85 kg."""
    result = ibw.weight_to_kg(154)
    assert math.isclose(result, 69.85, abs_tol=0.1), result


# ---------------------------------------------------------------------------
# Dosing weight recommendations
# ---------------------------------------------------------------------------

def test_dosing_normal_weight():
    """At 100% IBW, use actual weight."""
    wtype, _ = ibw.dosing_weight_recommendation(70, 70)
    assert wtype == "actual"


def test_dosing_underweight():
    """At <80% IBW, use actual weight."""
    wtype, _ = ibw.dosing_weight_recommendation(50, 70)
    assert wtype == "actual"


def test_dosing_overweight():
    """At 120-130% IBW, use IBW."""
    wtype, _ = ibw.dosing_weight_recommendation(88, 70)
    assert wtype == "ibw"


def test_dosing_obese():
    """At >130% IBW, use adjusted body weight."""
    wtype, _ = ibw.dosing_weight_recommendation(100, 70)
    assert wtype == "adjusted"


# ---------------------------------------------------------------------------
# Patient workflow
# ---------------------------------------------------------------------------

def test_calculate_patient_male():
    result = ibw.calculate_patient("P1", "M", 177.8, 80)
    assert result.ibw_devine is not None
    assert result.ibw_robinson is not None
    assert result.ibw_miller is not None
    assert result.ibw_hamwi is not None
    assert result.ibw_mean is not None
    assert result.percent_ibw is not None
    assert result.dosing_weight_type is not None


def test_calculate_patient_female():
    result = ibw.calculate_patient("P2", "F", 163, 60)
    assert result.ibw_devine is not None
    assert result.percent_ibw is not None


def test_calculate_patient_obese():
    """Obese patient should get adjusted BW."""
    result = ibw.calculate_patient("P3", "M", 175, 120)
    assert result.adjusted_bw is not None
    assert result.dosing_weight_type == "adjusted"
    assert result.weight_category == "Obese"


def test_calculate_patient_underweight():
    """Underweight patient."""
    result = ibw.calculate_patient("P4", "F", 165, 40)
    assert result.weight_category == "Underweight"
    assert result.dosing_weight_type == "actual"


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

def test_batch_csv():
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        out = os.path.join(tmp, "out.csv")
        with open(inp, "w", newline="") as f:
            f.write("patient_id,sex,height_cm,weight_kg,weight_unit\n")
            f.write("A1,M,175,80,kg\n")
            f.write("A2,F,163,55,kg\n")
        results = ibw.process_csv(inp, out)
        assert len(results) == 2
        assert results[0].ibw_devine is not None
        assert results[1].ibw_devine is not None
        assert os.path.exists(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_single():
    rc = ibw.main(["single", "--sex", "M", "--height", "175", "--weight", "80"])
    assert rc == 0


def test_cli_single_female():
    rc = ibw.main(["single", "--sex", "F", "--height", "163", "--weight", "55"])
    assert rc == 0


def test_cli_batch():
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        out = os.path.join(tmp, "out.csv")
        with open(inp, "w", newline="") as f:
            f.write("patient_id,sex,height_cm,weight_kg,weight_unit\n")
            f.write("T1,M,175,80,kg\n")
        rc = ibw.main(["batch", "--input", inp, "--output", out])
        assert rc == 0
        assert os.path.exists(out)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS: {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {t.__name__} -- {e}")
    print(f"\n{passed}/{passed + failed} tests passed.")
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(run_all())
