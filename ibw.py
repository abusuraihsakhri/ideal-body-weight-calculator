#!/usr/bin/env python3
"""
Ideal Body Weight (IBW) Calculator
====================================

Implements multiple IBW formulas:
  - Devine (1974):   M = 50 + 2.3×(H-60),  F = 45.5 + 2.3×(H-60)
  - Robinson (1983): M = 52 + 1.9×(H-60),  F = 49 + 1.7×(H-60)
  - Miller (1983):   M = 56.2 + 1.41×(H-60), F = 53.1 + 1.36×(H-60)
  - Hamwi (1964):    M = 48 + 2.7×(H-60),  F = 45.5 + 2.2×(H-60)

Plus adjusted body weight and dosing weight recommendations.

Stdlib only. Usage: python ibw.py --help
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------


def height_to_inches(height_cm: float) -> float:
    """Convert height from cm to inches."""
    return height_cm / 2.54


def weight_to_kg(weight_lbs: float) -> float:
    """Convert weight from pounds to kg."""
    return weight_lbs / 2.205


# ---------------------------------------------------------------------------
# IBW Formulas (all take height in inches, return kg)
# ---------------------------------------------------------------------------


def ibw_devine(height_inches: float, sex: str) -> float:
    """Devine (1974) formula.

    Male:   50 + 2.3 × (height_inches - 60)
    Female: 45.5 + 2.3 × (height_inches - 60)
    """
    sex = sex.upper()
    if sex == "M":
        return 50.0 + 2.3 * (height_inches - 60)
    elif sex == "F":
        return 45.5 + 2.3 * (height_inches - 60)
    else:
        raise ValueError(f"sex must be 'M' or 'F', got {sex!r}")


def ibw_robinson(height_inches: float, sex: str) -> float:
    """Robinson (1983) formula.

    Male:   52 + 1.9 × (height_inches - 60)
    Female: 49 + 1.7 × (height_inches - 60)
    """
    sex = sex.upper()
    if sex == "M":
        return 52.0 + 1.9 * (height_inches - 60)
    elif sex == "F":
        return 49.0 + 1.7 * (height_inches - 60)
    else:
        raise ValueError(f"sex must be 'M' or 'F', got {sex!r}")


def ibw_miller(height_inches: float, sex: str) -> float:
    """Miller (1983) formula.

    Male:   56.2 + 1.41 × (height_inches - 60)
    Female: 53.1 + 1.36 × (height_inches - 60)
    """
    sex = sex.upper()
    if sex == "M":
        return 56.2 + 1.41 * (height_inches - 60)
    elif sex == "F":
        return 53.1 + 1.36 * (height_inches - 60)
    else:
        raise ValueError(f"sex must be 'M' or 'F', got {sex!r}")


def ibw_hamwi(height_inches: float, sex: str) -> float:
    """Hamwi (1964) formula.

    Male:   48 + 2.7 × (height_inches - 60)
    Female: 45.5 + 2.2 × (height_inches - 60)
    """
    sex = sex.upper()
    if sex == "M":
        return 48.0 + 2.7 * (height_inches - 60)
    elif sex == "F":
        return 45.5 + 2.2 * (height_inches - 60)
    else:
        raise ValueError(f"sex must be 'M' or 'F', got {sex!r}")


FORMULAS = {
    "Devine": ibw_devine,
    "Robinson": ibw_robinson,
    "Miller": ibw_miller,
    "Hamwi": ibw_hamwi,
}


# ---------------------------------------------------------------------------
# Adjusted Body Weight
# ---------------------------------------------------------------------------


def adjusted_body_weight(actual_kg: float, ibw_kg: float) -> float:
    """Adjusted body weight = IBW + 0.4 × (actual - IBW).

    Used when actual weight > 130% of IBW for drug dosing.
    """
    return ibw_kg + 0.4 * (actual_kg - ibw_kg)


def percent_ibw(actual_kg: float, ibw_kg: float) -> float:
    """Calculate actual weight as a percentage of IBW."""
    if ibw_kg <= 0:
        raise ValueError(f"IBW must be positive, got {ibw_kg}")
    return (actual_kg / ibw_kg) * 100.0


# ---------------------------------------------------------------------------
# Dosing weight recommendations
# ---------------------------------------------------------------------------


def dosing_weight_recommendation(actual_kg: float, ibw_kg: float) -> tuple[str, str]:
    """Recommend which weight to use for drug dosing.

    Returns (recommended_weight_type, explanation).
    """
    pct = percent_ibw(actual_kg, ibw_kg)

    if pct < 80:
        return "actual", "Underweight (<80% IBW): use actual body weight"
    elif pct <= 120:
        return "actual", "Normal range (80-120% IBW): use actual body weight"
    elif pct <= 130:
        return "ibw", "Mildly overweight (120-130% IBW): use IBW to avoid overdosing"
    else:
        ajbw = adjusted_body_weight(actual_kg, ibw_kg)
        return "adjusted", (
            f"Obese (>130% IBW): use adjusted body weight ({ajbw:.1f} kg) "
            f"= IBW + 0.4 × (actual - IBW)"
        )


# ---------------------------------------------------------------------------
# Patient result
# ---------------------------------------------------------------------------


@dataclass
class IBWResult:
    patient_id: str
    sex: str
    height_cm: float
    height_inches: float
    actual_weight_kg: float
    ibw_devine: Optional[float] = None
    ibw_robinson: Optional[float] = None
    ibw_miller: Optional[float] = None
    ibw_hamwi: Optional[float] = None
    ibw_mean: Optional[float] = None
    adjusted_bw: Optional[float] = None
    percent_ibw: Optional[float] = None
    weight_category: Optional[str] = None
    dosing_weight_type: Optional[str] = None
    dosing_recommendation: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


def calculate_patient(
    patient_id: str,
    sex: str,
    height_cm: float,
    actual_weight_kg: float,
) -> IBWResult:
    """Calculate all IBW formulas, adjusted BW, and dosing recommendations."""
    sex = sex.upper()
    warnings: list[str] = []

    if sex not in ("M", "F"):
        warnings.append(f"Sex must be 'M' or 'F', got {sex!r}.")
    if height_cm <= 0:
        warnings.append(f"Height {height_cm} must be positive.")
    elif not (MIN_HEIGHT_CM <= height_cm <= MAX_HEIGHT_CM):
        warnings.append(
            f"Height {height_cm} cm is outside plausible range "
            f"({MIN_HEIGHT_CM}-{MAX_HEIGHT_CM} cm)."
        )
    if actual_weight_kg <= 0:
        warnings.append(f"Weight {actual_weight_kg} must be positive.")
    elif not (MIN_WEIGHT_KG <= actual_weight_kg <= MAX_WEIGHT_KG):
        warnings.append(
            f"Weight {actual_weight_kg} kg is outside plausible range "
            f"({MIN_WEIGHT_KG}-{MAX_WEIGHT_KG} kg)."
        )

    height_inches = height_to_inches(height_cm)

    result = IBWResult(
        patient_id=patient_id, sex=sex, height_cm=height_cm,
        height_inches=round(height_inches, 1),
        actual_weight_kg=actual_weight_kg, warnings=warnings,
    )

    if sex not in ("M", "F") or height_cm <= 0 or actual_weight_kg <= 0:
        return result

    # IBW formulas are only valid for heights >= 60 inches (152.4 cm)
    MIN_FORMULA_HEIGHT_CM = 152.4
    if height_cm < MIN_FORMULA_HEIGHT_CM:
        warnings.append(
            f"Height {height_cm} cm is below the minimum ({MIN_FORMULA_HEIGHT_CM} cm) "
            f"for which IBW formulas are valid. Results may be unreliable."
        )

    result.ibw_devine = round(max(0, ibw_devine(height_inches, sex)), 1)
    result.ibw_robinson = round(max(0, ibw_robinson(height_inches, sex)), 1)
    result.ibw_miller = round(max(0, ibw_miller(height_inches, sex)), 1)
    result.ibw_hamwi = round(max(0, ibw_hamwi(height_inches, sex)), 1)

    all_ibw = [result.ibw_devine, result.ibw_robinson, result.ibw_miller, result.ibw_hamwi]
    result.ibw_mean = round(sum(all_ibw) / len(all_ibw), 1)

    # Use Devine as the primary IBW for adjusted BW and dosing
    primary_ibw = result.ibw_devine
    if primary_ibw is not None and primary_ibw > 0:
        result.percent_ibw = round(percent_ibw(actual_weight_kg, primary_ibw), 1)

        if result.percent_ibw > 130:
            result.adjusted_bw = round(adjusted_body_weight(actual_weight_kg, primary_ibw), 1)

        # Weight category
        if result.percent_ibw < 80:
            result.weight_category = "Underweight"
        elif result.percent_ibw <= 120:
            result.weight_category = "Normal"
        elif result.percent_ibw <= 130:
            result.weight_category = "Overweight"
        else:
            result.weight_category = "Obese"

        # Dosing recommendation
        wtype, explanation = dosing_weight_recommendation(actual_weight_kg, primary_ibw)
        result.dosing_weight_type = wtype
        result.dosing_recommendation = explanation

    return result


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

CSV_INPUT_FIELDS = ["patient_id", "sex", "height_cm", "weight_kg", "weight_unit"]

CSV_OUTPUT_FIELDS = [
    "patient_id", "sex", "height_cm", "height_inches", "actual_weight_kg",
    "ibw_devine", "ibw_robinson", "ibw_miller", "ibw_hamwi", "ibw_mean",
    "adjusted_bw", "percent_ibw", "weight_category",
    "dosing_weight_type", "dosing_recommendation", "warnings",
]

# Physiological validation bounds
MIN_HEIGHT_CM = 30.0    # ~1 ft (neonate)
MAX_HEIGHT_CM = 272.0   # tallest recorded human
MIN_WEIGHT_KG = 0.5     # premature infant
MAX_WEIGHT_KG = 600.0   # extreme obesity upper bound


def _validate_path(path: str) -> str:
    """Validate that a path is safe (no directory traversal escapes)."""
    normalized = os.path.normpath(path)
    # Block paths that escape the current directory via ..
    if ".." in normalized.split(os.sep):
        raise ValueError(f"Path must not contain directory traversal (..): {path!r}")
    return normalized


def process_csv(input_path: str, output_path: str) -> list[IBWResult]:
    """Read patient rows from CSV, compute IBW for each, write results CSV."""
    results: list[IBWResult] = []
    input_path = _validate_path(input_path)
    output_path = _validate_path(output_path)

    with open(input_path, "r", newline="", encoding="utf-8-sig") as f_in:
        reader = csv.DictReader(f_in)
        missing = set(["patient_id", "sex", "height_cm", "weight_kg"]) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {sorted(missing)}")

        for row_num, row in enumerate(reader, start=2):
            patient_id = (row.get("patient_id") or "").strip() or f"row{row_num}"
            row_warnings: list[str] = []

            try:
                height_cm = float(row["height_cm"])
                weight_raw = float(row["weight_kg"])
            except (KeyError, ValueError, TypeError) as exc:
                row_warnings.append(f"Could not parse required fields: {exc}")
                results.append(IBWResult(patient_id=patient_id, sex="?", height_cm=0,
                                          height_inches=0, actual_weight_kg=0, warnings=row_warnings))
                continue

            sex = (row.get("sex") or "").strip().upper()
            weight_unit = (row.get("weight_unit") or "kg").strip().lower()

            if weight_unit in ("lb", "lbs", "pound", "pounds"):
                weight_kg = weight_to_kg(weight_raw)
            else:
                weight_kg = weight_raw

            result = calculate_patient(
                patient_id=patient_id, sex=sex,
                height_cm=height_cm, actual_weight_kg=weight_kg,
            )
            result.warnings = row_warnings + result.warnings
            results.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=CSV_OUTPUT_FIELDS)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "patient_id": r.patient_id,
                "sex": r.sex,
                "height_cm": r.height_cm,
                "height_inches": r.height_inches,
                "actual_weight_kg": r.actual_weight_kg,
                "ibw_devine": _fmt(r.ibw_devine),
                "ibw_robinson": _fmt(r.ibw_robinson),
                "ibw_miller": _fmt(r.ibw_miller),
                "ibw_hamwi": _fmt(r.ibw_hamwi),
                "ibw_mean": _fmt(r.ibw_mean),
                "adjusted_bw": _fmt(r.adjusted_bw),
                "percent_ibw": _fmt(r.percent_ibw),
                "weight_category": r.weight_category or "",
                "dosing_weight_type": r.dosing_weight_type or "",
                "dosing_recommendation": r.dosing_recommendation or "",
                "warnings": " | ".join(r.warnings),
            })

    return results


def _fmt(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.1f}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ibw",
        description="Ideal Body Weight Calculator (Devine, Robinson, Miller, Hamwi).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Calculate IBW for one patient")
    single.add_argument("--id", dest="patient_id", default="patient", help="Patient identifier")
    single.add_argument("--sex", required=True, choices=["M", "F", "m", "f"], help="Biological sex")
    single.add_argument("--height", type=float, required=True, help="Height in cm")
    single.add_argument("--weight", type=float, required=True, help="Actual weight in kg")

    batch = subparsers.add_parser("batch", help="Batch CSV processing")
    batch.add_argument("--input", required=True, help="Input CSV path")
    batch.add_argument("--output", required=True, help="Output CSV path")

    audit = subparsers.add_parser("audit", help="Run distributed component audit task")
    audit.add_argument("--task-id", default="AUDIT-TASK-01", help="Task identifier")

    chat = subparsers.add_parser("chat", help="Supervisory conversational assistant")
    chat.add_argument("query", nargs="*", help="Query string")

    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    return parser


def _print_single_result(result: IBWResult) -> None:
    print(f"Patient: {result.patient_id}  Sex: {result.sex}")
    print(f"  Height: {result.height_cm:.1f} cm ({result.height_inches:.1f} inches)")
    print(f"  Actual weight: {result.actual_weight_kg:.1f} kg")
    print(f"\n  Ideal Body Weight:")
    print(f"    Devine:    {_fmt(result.ibw_devine)} kg")
    print(f"    Robinson:  {_fmt(result.ibw_robinson)} kg")
    print(f"    Miller:    {_fmt(result.ibw_miller)} kg")
    print(f"    Hamwi:     {_fmt(result.ibw_hamwi)} kg")
    print(f"    Mean:      {_fmt(result.ibw_mean)} kg")
    print(f"\n  % IBW: {_fmt(result.percent_ibw)}%")
    print(f"  Weight category: {result.weight_category or 'N/A'}")
    if result.adjusted_bw is not None:
        print(f"  Adjusted body weight: {result.adjusted_bw:.1f} kg")
    print(f"\n  Dosing recommendation:")
    print(f"    Use: {result.dosing_weight_type or 'N/A'} weight")
    print(f"    {result.dosing_recommendation or 'N/A'}")

    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    - {w}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_patient(
            patient_id=args.patient_id, sex=args.sex,
            height_cm=args.height, actual_weight_kg=args.weight,
        )
        _print_single_result(result)
        return 0

    if args.command == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} patients -> {args.output}")
        return 0

    if args.command == "audit":
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier="CLI-AUDIT",
            primary_metric=10.0,
            secondary_metric=3.0,
        )
        dossier = supervisor.process_task(payload)
        print(f"Audit complete: {dossier.dossier_id} urgency={dossier.overall_urgency.value}")
        return 0

    if args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query) if args.query else "status"
        response = supervisor.query_supervisory_chat(query)
        print(response)
        return 0

    if args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        print(f"Audit trail integrity: {'VALID' if valid else 'COMPROMISED'}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
