.PHONY: help init lint mypy doctest unittest test segment downsamplee demo clean

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

opencv:
	git clone https://github.com/opencv/opencv.git --depth=1
	grep -qxF 'OPEN_CV_SAMPLES=$(CURDIR)/opencv/samples/data' .env || echo 'OPEN_CV_SAMPLES=$(CURDIR)/opencv/samples/data' >> .env

lint:
	pipenv run flake8 .

mypy:
	pipenv run mypy video_reuse_detector/*.py --ignore-missing-imports

doctest:
	pipenv run python -m doctest -v video_reuse_detector/*.py

unittest: opencv
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
segment: env
segment: interim
	@pipenv run python -m video_reuse_detector.segment $(INPUT_FILE) interim/$(FILENAME)

downsample: FILENAME=$(basename $(notdir $(INPUT_FILE)))
downsample: env
downsample: interim
	@pipenv run python -m video_reuse_detector.downsample interim/$(FILENAME) $(FILENAME)

demo: raw/dive.webm
demo: raw/caterpillar.webm
demo: interim
	pipenv run python -m video_reuse_detector.fingerprint raw/dive.webm interim/dive
	pipenv run python -m video_reuse_detector.fingerprint raw/caterpillar.webm interim/caterpillar

clean:
	@echo 'Cleaning out interim directory, leaving "raw" untouched'
	rm -rf interim
