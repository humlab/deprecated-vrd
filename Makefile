.PHONY: doctest lint mypy test

lint:
	pipenv run flake8 .

mypy:
	pipenv run mypy *.py --ignore-missing-imports

doctest:
	pipenv run python -m doctest -v *.py

test: lint
test: doctest
test: mypy
