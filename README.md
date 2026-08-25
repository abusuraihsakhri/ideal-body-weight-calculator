# Ideal Body Weight Calculator

Calculates ideal body weight using four published formulas, with adjusted body weight and drug dosing recommendations.

## Formulas Implemented

| Formula | Male | Female |
|:---|:---|:---|
| **Devine (1974)** | `50 + 2.3 × (H - 60)` | `45.5 + 2.3 × (H - 60)` |
| **Robinson (1983)** | `52 + 1.9 × (H - 60)` | `49 + 1.7 × (H - 60)` |
| **Miller (1983)** | `56.2 + 1.41 × (H - 60)` | `53.1 + 1.36 × (H - 60)` |
| **Hamwi (1964)** | `48 + 2.7 × (H - 60)` | `45.5 + 2.2 × (H - 60)` |

*H = height in inches*

### Adjusted Body Weight
```
AjBW = IBW + 0.4 × (actual_weight - IBW)
```
Used when actual weight > 130% of IBW.

### Dosing Weight Recommendations
| % IBW | Category | Weight for Dosing |
|:---:|:---|:---|
| < 80% | Underweight | Actual body weight |
| 80-120% | Normal | Actual body weight |
| 120-130% | Overweight | IBW |
| > 130% | Obese | Adjusted body weight |

## Usage

```bash
# Single patient
python ibw.py single --sex M --height 175 --weight 80

# Female patient
python ibw.py single --sex F --height 163 --weight 55

# Batch CSV processing
python ibw.py batch --input patients.csv --output results.csv
```

## CSV Input Format

Required: `patient_id`, `sex`, `height_cm`, `weight_kg`
Optional: `weight_unit` (kg/lb)

## Requirements

Python 3.9+ (stdlib only)

## Disclaimer

For educational and clinical decision support only. IBW formulas were developed from population data and may not apply to all individuals. Always use clinical judgment for drug dosing decisions.
