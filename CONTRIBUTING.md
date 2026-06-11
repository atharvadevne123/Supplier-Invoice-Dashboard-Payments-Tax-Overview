# Contributing to Supplier Invoice Dashboard

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/atharvadevne123/Supplier-Invoice-Dashboard-Payments-Tax-Overview.git
cd Supplier-Invoice-Dashboard-Payments-Tax-Overview
pip install -r requirements.txt
cp .env.example .env
python -m pytest
```

## Coding Standards

- Python 3.11+, type annotations required on all public functions
- Docstrings on all public classes and functions (Google style)
- No bare `except:` — always catch `Exception` or a specific type
- All I/O wrapped in try/except with `logging.exception`
- Run `ruff check . --select E,F,W,I --ignore E501 --fix` before committing

## Submitting Changes

1. Fork the repository and create a feature branch from `main`
2. Write tests covering your changes
3. Ensure `make lint` and `make test` pass
4. Open a pull request with a clear description of the change

## Reporting Issues

Please use the GitHub Issues tracker. Include steps to reproduce, expected behaviour, and actual behaviour.
