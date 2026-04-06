VIRTUAL_ENV_PATH=venv
SKIP_VENV="${NO_VENV}"
SHELL := /bin/bash
PYTHON := python3.11
SRC_ROOT := ./src
AZURE_PAT := "${PAT}"
SONARCUBE_URL="http://sonar.c-change-labs.lan"
SONARCUBE_VERSION="4.7"

.DEFAULT_GOAL := pre_commit

FORMAT_PATH := $(SRC_ROOT)
LINT_PATH := $(SRC_ROOT)
MYPY_PATH := $(SRC_ROOT)

POETRY := poetry
POETRY_GROUPS := dev

# Helper function to activate virtual environment if not skipped
define activate_venv
  if [ -z "$(SKIP_VENV)" ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi;
endef

pre_commit: pre_commit_hook lint

pre_commit_hook:
	@( \
		$(call activate_venv) \
		pre-commit run --all --hook-stage=commit; \
	)

verify-prerequisites:
	@(development/ensure-dependencies.sh)

setup: verify-prerequisites venv deps
	@( \
		$(call activate_venv) \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
		./development/install-cli-commands.sh "$(VIRTUAL_ENV_PATH)" "$(SRC_ROOT)"; \
		echo "DONE: setup" \
	)

deps:
	@( \
		set -e; \
		$(call activate_venv) \
		$(POETRY) install --all-extras --no-root; \
	)

deps-lock:
	@( \
		$(call activate_venv) \
		$(POETRY) lock; \
	)

# Synchronize installed dependencies to match the lock file
.PHONY: deps-sync
deps-sync:
	@( \
		$(call activate_venv) \
		set -e; \
		echo "Syncing dependencies..."; \
		$(POETRY) sync --all-extras --no-root --with "$(POETRY_GROUPS)"; \
		echo "DONE: all dependencies are synchronized"; \
	)

deps-update:
	@( \
		$(call activate_venv) \
		$(POETRY) lock; \
	)

deps-tree:
	@( \
		$(call activate_venv) \
		$(POETRY) show --tree; \
	)

.PHONY: venv
venv:
	@( \
	  	set -e; \
		$(PYTHON) -m venv $(VIRTUAL_ENV_PATH); \
		source ./venv/bin/activate; \
	)

copyright:
	@( \
       $(call activate_venv) \
       echo "Applying copyright..."; \
       for p in $(FORMAT_PATH); do \
       	 licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -d $$p; \
       done; \
       echo "DISABLED: copyright"; \
    )

ruff-fix-pyupgrade:
	@( \
	   $(call activate_venv) \
       echo "Applying pyupgrade..."; \
       ruff check --select UP --fix; \
       echo "DONE: pyupgrade"; \
    )

.PHONY: ruff-fix-pyupgrade-unsafe
ruff-fix-pyupgrade-unsafe:
	@( \
	   $(call activate_venv) \
	   echo "Applying pyupgrade..."; \
	   ruff check --select UP --fix --unsafe-fixes; \
	   echo "DONE: pyupgrade"; \
	)

ruff-format:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff code formatter..."; \
	   ruff format $(FORMAT_PATH); \
	   echo "DONE: Ruff"; \
	)

ruff-format-check:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff format check..."; \
	   ruff format --diff $(FORMAT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff import sort..."; \
	   ruff check --select I --fix; \
	   echo "DONE: Ruff"; \
	)

ruff-import-sort-check:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff import sort..."; \
	   ruff check --select I || exit 1; \
	   echo "DONE: Ruff"; \
	)

ruff-lint:
	@( \
	   $(call activate_venv) \
	   echo "Running Ruff lint..."; \
	   ruff check $(LINT_PATH) || exit 1; \
	   echo "DONE: Ruff"; \
	)

format: ruff-import-sort ruff-format
check-format: ruff-import-sort-check ruff-format-check

mypy:
	@( \
       set -e; \
       $(call activate_venv) \
       echo "Running MyPy checks..."; \
       mypy $(MYPY_PATH); \
       echo "DONE: MyPy"; \
    )

lint: ruff-lint mypy check-format

build:
	@( \
		echo "Building packages"; \
		set -e; \
		$(call activate_venv) \
		rm -rf dist/*; \
		$(POETRY) build; \
		echo "DONE: Building packages"; \
	)

publish: build
	@( \
		echo "Publishing packages"; \
		set -e; \
		$(call activate_venv) \
		$(POETRY) publish; \
		echo "DONE: Publishing packages"; \
	)

 test-publish: build
	@( \
		echo "Publishing packages to the TEST PYPI"; \
		set -e; \
		$(call activate_venv) \
		$(POETRY) publish -r test-pypi; \
		echo "DONE: Publishing packages (TEST PYPI)"; \
	)
private-publish: build
	@( \
		echo "Publishing packages"; \
		set -e; \
		$(call activate_venv) \
		$(POETRY) publish  --repository private; \
		echo "DONE: Publishing packages"; \
	)

coverage:
	@( \
		echo "Running coverage"; \
		set -e; \
		$(call activate_venv) \
		coverage run --source $(SRC_ROOT)/cqd_etl -m pytest; \
		coverage html; \
		echo "DONE: Coverage"; \
	)

test:
	@( \
		echo "Running tests"; \
		set -e; \
		$(call activate_venv) \
		echo pytest -v --cov-report term-missing --cov=$(SRC_ROOT)/cqd_etl; \
		pytest -v; \
		echo "DONE: Tests"; \
	)

changelog:
	@( \
		echo "Generating changelog"; \
		set -e; \
		$(call activate_venv) \
		cz changelog --incremental; \
		echo "DONE: Changelog"; \
	)

print-changelog:
	@( \
		$(call activate_venv) \
		cz changelog --dry-run --incremental; \
	)

release:
	@( \
		echo "Preparing release"; \
		set -e; \
		$(call activate_venv) \
		cz bump --changelog; \
		echo "DONE: Preparing release"; \
	)

print-version:
	@( \
		$(call activate_venv) \
		cz version --project; \
	)
