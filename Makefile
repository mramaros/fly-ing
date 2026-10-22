install:


run:


debug:


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any--warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs


lint-strict:
	flake8 .
	mypy . --strict --ignore-missing-imports
