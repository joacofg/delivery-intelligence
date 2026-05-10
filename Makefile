PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: bootstrap scrape smoke-live demo-live live-all analyze report all test clean

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && python -m pip install --upgrade pip
	$(ACTIVATE) && python -m pip install -e ".[dev]"
	$(ACTIVATE) && python -m playwright install chromium

scrape:
	$(ACTIVATE) && python -m ci scrape --mode live

smoke-live:
	$(ACTIVATE) && python -m ci scrape --mode live --platform rappi --address-id roma-001 --debug-evidence

demo-live:
	$(ACTIVATE) && python -m ci scrape --mode live --debug-evidence

live-all:
	$(ACTIVATE) && python -m ci scrape --mode live --all-addresses

analyze:
	$(ACTIVATE) && python -m ci analyze

report:
	$(ACTIVATE) && python -m ci report

all:
	$(ACTIVATE) && python -m ci scrape --mode snapshot
	$(ACTIVATE) && python -m ci analyze
	$(ACTIVATE) && python -m ci report

test:
	$(ACTIVATE) && pytest -q

clean:
	rm -rf $(VENV) .pytest_cache build dist *.egg-info
