### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

# See https://github.com/plone/code-quality
# Our configuration is in pyproject.toml.
CODE_QUALITY_VERSION=2.0.0
CURRENT_USER=$$(whoami)
USER_INFO=$$(id -u ${CURRENT_USER}):$$(id -g ${CURRENT_USER})
LINT=docker run --rm -v "$(PWD)":/github/workspace plone/code-quality:${CODE_QUALITY_VERSION} check
FORMAT=docker run --user="${USER_INFO}" --rm -v "$(PWD)":/github/workspace plone/code-quality:${CODE_QUALITY_VERSION} format

PACKAGE_NAME=plone.dexterity
PACKAGE_PATH=plone/
CHECK_PATH=setup.py $(PACKAGE_PATH)

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: format
format:  ## Format the codebase according to our standards
	$(FORMAT)

.PHONY: lint
lint:  ## validate with isort, black, flake8, pyroma, zpretty
	$(LINT)
