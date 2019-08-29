.PHONY: lint test

lint:
	pipenv run flake8 .

doctest:
	pipenv run python -m doctest -v *.py

test: lint
test: doctest
