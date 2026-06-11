.PHONY: install test lint run docker-build docker-up clean

install:
	pip install -r requirements.txt

test:
	python -m pytest -v --tb=short

lint:
	ruff check . --select E,F,W,I --ignore E501
	ruff check . --select E,F,W,I --ignore E501 --fix

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t supplier-invoice-dashboard .

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f supplier_invoices.db test_invoices.db
	rm -rf dist/ build/ *.egg-info/
