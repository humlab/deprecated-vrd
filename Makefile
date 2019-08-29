.PHONY: lint test

lint:
	pipenv run flake8 .

test:
	pipenv run python -m doctest -v *.py
