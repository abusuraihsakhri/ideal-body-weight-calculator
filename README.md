# Ideal Body Weight Calculator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)

Clinical decision support tool for calculating Ideal Body Weight (IBW) using multiple validated formulas, with adjusted body weight and dosing weight recommendations.

---

## 📖 What It Does

Implements four widely-used IBW formulas:

| Formula | Male | Female |
|---------|------|--------|
| Devine (1974) | 50 + 2.3×(H-60) | 45.5 + 2.3×(H-60) |
| Robinson (1983) | 52 + 1.9×(H-60) | 49 + 1.7×(H-60) |
| Miller (1983) | 56.2 + 1.41×(H-60) | 53.1 + 1.36×(H-60) |
| Hamwi (1964) | 48 + 2.7×(H-60) | 45.5 + 2.2×(H-60) |

All formulas take height in inches and return weight in kg. Plus adjusted body weight and dosing weight recommendations.

---

## ⚙️ Core Features

- **Single patient calculation** — compute all four IBW formulas, adjusted BW, and dosing recommendations
- **Batch CSV processing** — process multiple patients from a CSV file
- **Unit conversion** — automatic conversion between cm/inches and kg/lbs
- **Dosing recommendations** — weight-based drug dosing guidance
- **Input validation** — physiological range checks for height and weight
- **PHI guard** — outbound data inspection to prevent protected health information leakage
- **Audit trail** — HMAC-SHA256 tamper-evident logging

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/ideal-body-weight-calculator.git
cd ideal-body-weight-calculator

# Optional: create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (for web API and tests)
pip install -r requirements.txt

# Set the audit secret key (required for audit features)
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32)")
```

---

## 🚀 Usage

### Single Patient Calculation

```bash
python cli.py single --sex M --height 175 --weight 80
python cli.py single --id P001 --sex F --height 163 --weight 55
```

### Batch CSV Processing

```bash
python cli.py batch --input sample.csv --output results.csv
```

Input CSV format:

```csv
patient_id,sex,height_cm,weight_kg,weight_unit
P001,M,175,80,kg
P002,F,163,55,kg
P003,M,180,200,kg
P004,F,150,130,lbs
```

### Audit Commands

```bash
python cli.py audit --task-id TASK-001
python cli.py chat "Explain specifications"
python cli.py verify-audit
```

### Web API (requires FastAPI)

```bash
uvicorn agents.api:app --reload
```

Then open http://localhost:8000/health or http://localhost:8000/api/audit

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run core IBW tests only
python test_ibw.py

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 🐳 Docker

```bash
# Build and run
docker build -t ideal-body-weight-calculator .
docker run -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32)") ideal-body-weight-calculator

# Or use docker-compose
cp .env.example .env
# Edit .env and set AUDIT_SECRET_KEY
docker-compose up
```

---

## 🛡️ Security

- **PHI Outbound Guard**: Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs
- **Input Validation**: Path traversal protection, physiological range checks
- **No Hardcoded Secrets**: All secrets via environment variables

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
