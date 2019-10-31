.PHONY: help init lint mypy doctest unittest test segment downsample demo clean pipelinetest

SHELL=/bin/bash

help:
	@echo '    init'
	@echo '        install pipenv and all project dependencies'
	@echo '    lint'
	@echo '        run python linting checks'
	@echo '    mypy'
	@echo '        run python typechecks'
	@echo '    doctest'
	@echo '        run python doctests'
	@echo '    unittest'
	@echo '        run python doctests'
	@echo '    test'
	@echo '        run all tests (including lint/type checks)'
	@echo '    opencv'
	@echo '        download opencv to access sample data (needed for tests)'

init:
	@echo 'Install python dependencies'
	pip3 install pipenv
	pipenv --python python3.7
	pipenv install --dev

.env:
	@touch $@
	@echo 'APP_SETTINGS="app.config.DevelopmentConfig"' >> $@
	@echo 'DATABASE_URL="postgres://sid:sid12345@localhost:5432/video_reuse_detector"' >> $@

opencv: .env
	@if [[ ! -d "$@" ]]; then\
		git clone https://github.com/opencv/opencv.git --depth=1 $@;\
	fi

    # Check if the path to the samples have already been added,
    # otherwise add it in
	grep -qxF 'OPEN_CV_SAMPLES=$(CURDIR)/$@/samples/data' .env || echo 'OPEN_CV_SAMPLES=$(CURDIR)/$@/samples/data' >> .env

lint:
	pipenv run flake8 .

mypy:
	pipenv run mypy video_reuse_detector --ignore-missing-imports
	pipenv run mypy app --ignore-missing-imports

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

raw/Megamind.avi: raw
raw/Megamind.avi: opencv
	ln -f opencv/samples/data/Megamind.avi raw/Megamind.avi

raw/Megamind_flipped.avi: raw/Megamind.avi
	ffmpeg -i $< -vf hflip -c:a copy $@

raw/Megamind_bugy.avi: raw
raw/Megamind_bugy.avi: opencv
	ln -f opencv/samples/data/Megamind_bugy.avi raw/Megamind_bugy.avi

raw/dive.webm: raw
	curl -C - "https://upload.wikimedia.org/wikipedia/commons/6/6f/Ex1402-dive11_fish.webm" --output $@

raw/caterpillar.webm: raw
	curl -C - "https://upload.wikimedia.org/wikipedia/commons/a/af/Caterpillar_%28Danaus_chrysippus%29.webm" --output $@

raw/Reference.zip: raw
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Reference.zip" --output $@

raw/ReTRiEVED-Reference: raw/Reference.zip
	unzip -jn $< -d $@

raw/PLR.zip: raw
	curl -C - "http://www.comlab.uniroma3.it/retrieved/PLR.zip" --output $@

raw/ReTRiEVED-PLR: raw/PLR.zip
	unzip -jn $< -d $@

raw/Jitter.zip: raw
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Jitter.zip" --output $@

raw/ReTRiEVED-Jitter: raw/Jitter.zip
	unzip -jn $< -d $@

raw/Delay.zip: raw
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Delay.zip" --output $@

raw/ReTRiEVED-Delay: raw/Delay.zip
	unzip -jn $< -d $@

raw/Throughput.zip : raw
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Throughput.zip" --output $@

raw/ReTRiEVED-Throughput: raw/Throughput.zip
	unzip -jn $< -d $@

ReTRiEVED: raw/ReTRiEVED-Reference
ReTRiEVED: raw/ReTRiEVED-PLR
ReTRiEVED: raw/ReTRiEVED-Jitter
ReTRiEVED: raw/ReTRiEVED-Delay
ReTRiEVED: raw/ReTRiEVED-Throughput
	./parallel_process.sh $^ > ReTRiEVED-stdout.log 2>ReTriEVED-stderr.log

segment: FILENAME=$(basename $(notdir $(INPUT_FILE)))
segment: interim
	@>&2 echo "Segmenting $(INPUT_FILE) FILENAME=$(FILENAME)" 
	@pipenv run python -m video_reuse_detector.segment $(INPUT_FILE) interim/$(FILENAME)

downsample: TARGET_DIRECTORY=$(dir $(INPUT_FILE))
downsample: interim
	@echo "Downsampling $(INPUT_FILE). Expect output at $(TARGET_DIRECTORY)"
	@pipenv run python -m video_reuse_detector.downsample $(INPUT_FILE)

process: interim
	./process.sh $(INPUT_FILE)

run:
	@echo "Comparing $(QUERY_VIDEO) to $(REFERENCE_VIDEO)"
	pipenv run python -m video_reuse_detector.main $(QUERY_VIDEO) $(REFERENCE_VIDEO)

audio: TARGET_DIRECTORY=$(dir $(INPUT_FILE))
audio: interim
	@echo "Extracting audio from $(INPUT_FILE). Expect output at $(TARGET_DIRECTORY)"
	@pipenv run python -m video_reuse_detector.extract_audio "$(INPUT_FILE)"

clean:
	@echo 'Cleaning out log and txt files'
	rm -rf -- *.log
	rm -rf -- *.txt
