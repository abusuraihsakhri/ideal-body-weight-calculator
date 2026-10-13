# Ideal Body Weight Calculator

A lightweight adult ideal-body-weight (IBW) calculator, usable in a browser, through a Python CLI, or via a FastAPI endpoint. The browser version runs entirely on the device with no server or external dependencies.

## Calculations

All formulas use height in **inches** and return **kilograms**. H is height in inches.

| Formula | Male coefficient | Female coefficient |
| --- | --- | --- |
| Devine (1974) | 50 + 2.3 × (H − 60) | 45.5 + 2.3 × (H − 60) |
| Robinson (1983) | 52 + 1.9 × (H − 60) | 49 + 1.7 × (H − 60) |
| Miller (1983) | 56.2 + 1.41 × (H − 60) | 53.1 + 1.36 × (H − 60) |
| Hamwi (1964) | 48 + 2.7 × (H − 60) | 45.5 + 2.2 × (H − 60) |

The calculator also shows the mean of four rounded estimates, actual weight as a percentage of **Devine** IBW, and conditional adjusted weight: `Devine IBW + 0.4 × (actual − Devine IBW)` if actual weight exceeds 130% of Devine IBW.

**Clinical limits:** The browser and Python patient workflow do not extrapolate IBW formulas below 152.4 cm (5 ft). These are adult reference-weight equations, not diagnoses of obesity, measured body composition, treatment targets, or universal medication-dosing recommendations. The original Python CLI includes an illustrative weight-selection heuristic; it must **not** be used to choose a drug dose without the appropriate medication-specific protocol.

## Browser calculator

The static files in `web/` provide:

- Single-patient calculation with centimetres/inches and kilograms/pounds
- Devine, Robinson, Miller and Hamwi estimates
- Local batch CSV processing (1,000 rows / 2 MB maximum) with downloadable results and validation errors
- Input validation and spreadsheet-formula escaping for exported identifiers

Open `web/index.html` through a local HTTP server (ES modules do not work reliably from `file://`):

```bash
python -m http.server 8080 --directory web
```

Open http://localhost:8080. On GitHub Pages, the same folder is deployed by the CI workflow once Pages publishing is enabled.

## Python CLI and API

Python 3.10+ required. Core `ibw.py` calculations use only the standard library.

```bash
git clone https://github.com/abusuraihsakhri/ideal-body-weight-calculator.git
cd ideal-body-weight-calculator
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python cli.py single --sex M --height 175 --weight 80
python cli.py batch --input sample.csv --output results.csv

uvicorn agents.api:app --reload
```

The API serves the browser at http://localhost:8000/ and exposes:

- `POST /api/ibw` with JSON `{"sex":"M","height_cm":175,"weight_kg":80}`
- `GET /health`
- Interactive API documentation at `/docs`

Optional experimental audit and demonstration-chat endpoints remain in `agents/`. They are **not** part of the IBW calculation. Audit writes require a secret:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id TEST-001
python cli.py verify-audit
```

Audit records are held **in memory**, not persisted across restarts. The HMAC chain detects modification within the retained ledger but does not provide durable, independent audit storage. The optional PHI-pattern filter is heuristic and must not be treated as a guarantee of de-identification or regulatory compliance.

## Batch CSV schema

```csv
patient_id,sex,height_cm,weight_kg,weight_unit
case01,M,175,80,kg
case02,F,163,130,lb
```

`sex`, `height_cm`, `weight_kg` are required. `weight_unit` defaults to kg and accepts kg, lb, lbs, pound or pounds. `patient_id` is optional in the browser. Use anonymous row labels, not patient identifiers.

## Privacy and security

Browser data is processed locally: no remote API requests, cookies, or local storage. Files are read only when selected, and output is downloaded only on request. **The Python API is a separate service**; if deployed, operators are responsible for transport security, access control, and appropriate data-handling policies. No credentials are bundled into client-side code.

## Tests and Docker

```bash
python -m pytest -q
python test_ibw.py
node --test tests/test_web.mjs

docker build -t ideal-body-weight-calculator .
docker run -p 8000:8000 ideal-body-weight-calculator
```

CI tests Python 3.10–3.12, Node JavaScript, API HTTP behavior, Docker, and installed dependency vulnerabilities. It also includes a GitHub Pages deployment job for `master`.

## Compatibility and license

Python 3.10+; recent browsers supporting ES modules, `File.text()`, and `Blob`. No Pyodide download is needed because the four browser equations are implemented directly in JavaScript and regression-tested against Python reference cases.

MIT license; see [LICENSE](LICENSE).
