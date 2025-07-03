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

pre_commit: pre_commit_hook lint

pre_commit_hook:
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		pre-commit run --all --hook-stage=commit; \
	)

verify-prerequisites:
	@(development/ensure-dependencies.sh)

setup: verify-prerequisites venv deps
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
		./development/install-cli-commands.sh "$(VIRTUAL_ENV_PATH)" "$(SRC_ROOT)"; \
		echo "DONE: setup" \
	)

deps:
	@( \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		$(POETRY) install --all-extras --no-root; \
	)

deps-lock:
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
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
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		$(POETRY) lock; \
	)

deps-tree:
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
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
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Applying copyright..."; \
       for p in $(FORMAT_PATH); do \
       	 licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -d $$p; \
       done; \
       echo "DISABLED: copyright"; \
    )

black:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running Black code formatter..."; \
       black $(FORMAT_PATH); \
       \
       echo "DONE: Black"; \
    )

black-check:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       set -e; \
       echo "Running Black format check..."; \
       black --check $(FORMAT_PATH); \
       \
       echo "DONE: Black format check"; \
    )

isort:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running isort formatter..."; \
       isort $(FORMAT_PATH); \
       \
       echo "DONE: isort formatter"; \
    )

isort-check:
	@( \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       set -e; \
       echo "Running isort validation..."; \
       isort --check $(FORMAT_PATH); \
       \
       echo "DONE: isort validation"; \
    )

format: isort black
check-format: isort-check black-check

flake8:
	@( \
       set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running Flake8 checks..."; \
       flake8 $(LINT_PATH) --count --statistics; \
       echo "DONE: Flake8"; \
    )

mypy:
	@( \
       set -e; \
       if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
       echo "Running MyPy checks..."; \
       mypy $(MYPY_PATH); \
       echo "DONE: MyPy"; \
    )

lint: flake8 mypy check-format

build:
	@( \
		echo "Building packages"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		rm -rf dist/*; \
		$(POETRY) build; \
		echo "DONE: Building packages"; \
	)

publish: build
	@( \
		echo "Publishing packages"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		$(POETRY) publish; \
		echo "DONE: Publishing packages"; \
	)

 test-publish: build
	@( \
		echo "Publishing packages to the TEST PYPI"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		$(POETRY) publish -r test-pypi; \
		echo "DONE: Publishing packages (TEST PYPI)"; \
	)
private-publish: build
	@( \
		echo "Publishing packages"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		$(POETRY) publish  --repository private; \
		echo "DONE: Publishing packages"; \
	)

coverage:
	@( \
		echo "Running coverage"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		coverage run --source $(SRC_ROOT)/cqd_etl -m pytest; \
		coverage html; \
		echo "DONE: Coverage"; \
	)

test:
	@( \
		echo "Running tests"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		echo pytest -v --cov-report term-missing --cov=$(SRC_ROOT)/cqd_etl; \
		pytest -v; \
		echo "DONE: Tests"; \
	)

changelog:
	@( \
		echo "Generating changelog"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		cz changelog --incremental; \
		echo "DONE: Changelog"; \
	)

print-changelog:
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		cz changelog --dry-run --incremental; \
	)

release:
	@( \
		echo "Preparing release"; \
		set -e; \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		cz bump --changelog; \
		echo "DONE: Preparing release"; \
	)

print-version:
	@( \
		if [ -z $(SKIP_VENV) ]; then source $(VIRTUAL_ENV_PATH)/bin/activate; fi; \
		cz version --project; \
	)
