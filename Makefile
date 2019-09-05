.PHONY: doctest lint mypy test unittest

lint:
	pipenv run flake8 .

mypy:
	pipenv run mypy video_reuse_detector/*.py --ignore-missing-imports

doctest:
	pipenv run python -m doctest -v video_reuse_detector/*.py

unittest:
	pipenv run python -m unittest tests.tests.TestColorCorrelation

test: doctest
test: mypy
test: unittest
test: lint
