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

raw:
	@mkdir $@

interim:
	@mkdir $@

raw/dive.webm: raw
	curl "https://upload.wikimedia.org/wikipedia/commons/6/6f/Ex1402-dive11_fish.webm" --output $@

raw/caterpillar.webm: raw
	curl "https://upload.wikimedia.org/wikipedia/commons/a/af/Caterpillar_%28Danaus_chrysippus%29.webm" --output $@

segment: FILENAME=$(basename $(notdir $(INPUT_FILE)))
segment: interim
	@pipenv run python -m video_reuse_detector.segment $(INPUT_FILE) interim/$(FILENAME)

downsample: FILENAME=$(basename $(notdir $(INPUT_FILE)))
downsample: interim
	@pipenv run python -m video_reuse_detector.downsample interim/$(FILENAME) $(FILENAME)

demo: dive.webm caterpillar.webm
	pipenv run python -m video_reuse_detector.fingerprint dive.webm dive
	pipenv run python -m video_reuse_detector.fingerprint caterpillar.webm caterpillar

clean:
	rm -rf dive
	rm -rf caterpillar

help:
	@echo '    init'
	@echo '        install pipenv and all project dependencies'
	@echo '    test'
	@echo '        run all tests'

init:
	@echo 'Install python dependencies'
	pip3 install pipenv
	pipenv --python python3.7
	pipenv install --dev

