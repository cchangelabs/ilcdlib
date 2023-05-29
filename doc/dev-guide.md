# Developer's Guide

## Setup Dev Environment

### Requirements

* Python 3.11+
* sed
* make

### Setup

1. Checkout repository source code.
2. Run setup script `make setup`. It should create virtual environment, install all dependencies
   and set all configurations.

### Useful commands

1. Run tests: `make test`
1. Do all required pre-commit checks: `make`
1. Run linter for all project: `make lint`
1. Build a wheel: `make build`
1. Updage library versions according to constrainst (update lock file): `make deps-lock`
1. Install\update dependancies `make deps`
1. Print change log for the unreleased version: `make print-changelog`
1. Create a release commit: `make release` (**do not run it locally**, see [release guide](release.md) instead)
