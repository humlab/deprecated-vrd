.PHONY: doctest lint mypy test unittest demo clean

lint:
	pipenv run flake8 .

mypy:
	pipenv run mypy video_reuse_detector/*.py --ignore-missing-imports

doctest:
	pipenv run python -m doctest -v video_reuse_detector/*.py

unittest:
	pipenv run python -m unittest discover -s tests

test: doctest
test: mypy
test: unittest
test: lint

dive.webm:
	curl "https://upload.wikimedia.org/wikipedia/commons/6/6f/Ex1402-dive11_fish.webm" --output $@

caterpillar.webm:
	curl "https://upload.wikimedia.org/wikipedia/commons/a/af/Caterpillar_%28Danaus_chrysippus%29.webm" --output $@

demo: dive.webm caterpillar.webm
	pipenv run python -m video_reuse_detector.main dive.webm dive
	pipenv run python -m video_reuse_detector.main caterpillar.webm caterpillar

clean:
	rm -rf dive
	rm -rf caterpillar
