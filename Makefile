VENV_DIR ?= C:/dev/venvs/ai-analysis-audit
SYSTEM_PYTHON ?= python
PYTHON ?= $(VENV_DIR)/Scripts/python.exe
CASE ?= 01_bank_marketing

.PHONY: venv install data olist-data olist-analysis reference-notebooks results reports test lint validate-prompts validate-output run-ai-code all

venv:
	$(SYSTEM_PYTHON) -m venv "$(VENV_DIR)"

install:
	"$(PYTHON)" -m pip install -r requirements.txt

data:
	"$(PYTHON)" src/fetch_data.py

olist-data:
	"$(PYTHON)" src/fetch_olist.py

olist-analysis: olist-data
	"$(PYTHON)" src/olist_delivery.py

reference-notebooks: data
	"$(PYTHON)" src/execute_reference_notebooks.py

results: reference-notebooks
	"$(PYTHON)" src/build_case_results.py

reports: results
	"$(PYTHON)" src/build_reports.py
	"$(PYTHON)" src/verify_numbers.py

test:
	"$(PYTHON)" -m pytest tests -q

lint:
	"$(PYTHON)" -m ruff check src tests

validate-prompts: data
	"$(PYTHON)" src/validate_ai_outputs.py --check-prompts

validate-output:
	"$(PYTHON)" src/validate_ai_outputs.py "$(CASE)"

run-ai-code:
	"$(PYTHON)" src/run_ai_code.py --case "$(CASE)"

all: test lint reports