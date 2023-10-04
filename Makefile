##############################################################################
# Common make values.
.DEFAULT_GOAL := run
package       := textual_key_recorder
code          := src/$(package)
run           := poetry run
python        := $(run) python
textual       := $(run) textual
lint          := $(run) pylint
mypy          := $(run) mypy
black         := $(run) black
isort         := $(run) isort

##############################################################################
# Run the app.
.PHONY: run
run:
	$(python) -m $(package)

##############################################################################
# Setup/update packages the system requires.
.PHONY: setup
setup:				# Set up the development environment
	poetry install
	$(run) pre-commit install

.PHONY: update
update:			# Update the development environment
	poetry update

##############################################################################
# Reformatting tools.
.PHONY: black
black:				# Run black over the code
	$(black) $(code) $(examples)

.PHONY: isort
isort:				# Run isort over the code
	$(isort) --profile black $(code) $(examples)

.PHONY: reformat
reformat: isort black		# Run all the formatting tools over the code

##############################################################################
# Checking/testing/linting/etc.
.PHONY: lint
lint:				# Run Pylint over the library
	$(lint) $(code) $(examples)

.PHONY: typecheck
typecheck:			# Perform static type checks with mypy
	$(mypy) --scripts-are-modules $(code) $(examples)

.PHONY: stricttypecheck
stricttypecheck:	        # Perform strict static type checks with mypy
	$(mypy) --scripts-are-modules --strict $(code) $(examples)

.PHONY: checkall
checkall: lint stricttypecheck	# Check all the things

##############################################################################
# Utility.
.PHONY: repl
repl:				# Start a Python REPL
	$(python)

.PHONY: shell
shell:				# Create a shell within the virtual environment
	poetry shell

.PHONY: help
help:				# Display this help
	@grep -Eh "^[a-z]+:.+# " $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.+# "}; {printf "%-20s %s\n", $$1, $$2}'

##############################################################################
# Housekeeping tasks.
.PHONY: housekeeping
housekeeping:			# Perform some git housekeeping
	git fsck
	git gc --aggressive
	git remote update --prune
