PYTHON ?= python3
MAP    ?= maps/easy/02_simple_fork.txt
MOVES  ?= solutions/easy_02_simple_fork.moves

install:
	$(PYTHON) -m pip install -r requirements.txt flake8 mypy

run:
	$(PYTHON) -m viewer3d $(MAP) $(MOVES)

debug:
	$(PYTHON) -m pdb -m viewer3d $(MAP) $(MOVES)

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf .mypy_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict --ignore-missing-imports

.PHONY: install run debug clean lint lint-strict
