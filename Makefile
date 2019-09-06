.PHONY: doctest lint mypy test unittest demo

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

dive.webm:
	curl "https://upload.wikimedia.org/wikipedia/commons/6/6f/Ex1402-dive11_fish.webm" --output dive.webm

demo: dive.webm
	pipenv run python -m video_reuse_detector.main dive.webm demo

clean:
	rm -rf demo
