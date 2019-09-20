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
segment: interim
	@>&2 echo "Segmenting $(INPUT_FILE) FILENAME=$(FILENAME)" 
	@pipenv run python -m video_reuse_detector.segment $(INPUT_FILE) interim/$(FILENAME)

downsample: TARGET_DIRECTORY=$(dir $(INPUT_FILE))
downsample: interim
	@echo "Downsampling $(INPUT_FILE). Expect output at $(TARGET_DIRECTORY)"
	@pipenv run python -m video_reuse_detector.downsample $(INPUT_FILE)

process: FILENAME=$(basename $(notdir $(INPUT_FILE)))
process: SEGMENTS_TXT="$(FILENAME)-segments.txt"
process: FRAMES_TXT="$(FILENAME)-frames.txt"
process: KEYFRAMES_TXT="$(FILENAME)-keyframes.txt"
process: AUDIO_TXT="$(FILENAME)-audio.txt"
process: PROCESSED_DIR="processed"
process: SOURCES="$(FILENAME)-sources.txt"
process: TARGETS="$(FILENAME)-targets.txt"
process: interim
	@echo "Processing $(FILENAME)"

	@echo "Producing segments from $(FILENAME), output in $(SEGMENTS_TXT)"
	@make --no-print-directory segment > $(SEGMENTS_TXT)

	@echo "Calling video_reuse_detector.downsample on each line in \"$(SEGMENTS_TXT)\". Output can be read from \"$(FRAMES_TXT)\""
	@cat $(SEGMENTS_TXT) | xargs pipenv run python -m video_reuse_detector.downsample > $(FRAMES_TXT)

	@echo "Calling video_reuse_detector.keyframe on each group of five lines in \"$(FRAMES_TXT)\". Output can be read from \"$(KEYFRAMES_TXT)\""
	@cat $(FRAMES_TXT) | xargs -n 5 pipenv run python -m video_reuse_detector.keyframe > $(KEYFRAMES_TXT)

	@echo "Calling video_reuse_detector.extract_audio on each line in \"$(SEGMENTS_TXT)\". Output can be read from \"$(AUDIO_TXT)\""
	@cat $(SEGMENTS_TXT) | xargs pipenv run python -m video_reuse_detector.extract_audio > $(AUDIO_TXT)
	@echo "Creating the directory \"$(PROCESSED_DIR)\" if it does not exist"
	@mkdir -p "$(PROCESSED_DIR)"

	@echo "Copying files listed in \"$(KEYFRAMES_TXT)\" and \"$(AUDIO_TXT)\" to \"$(PROCESSED_DIR)\""
	@cat $(KEYFRAMES_TXT) $(AUDIO_TXT) > $(SOURCES)
	./transfer_interim.sh "$(SOURCES)" "$(TARGETS)"

audio: TARGET_DIRECTORY=$(dir $(INPUT_FILE))
audio: interim
	@echo "Extracting audio from $(INPUT_FILE). Expect output at $(TARGET_DIRECTORY)"
	@pipenv run python -m video_reuse_detector.extract_audio "$(INPUT_FILE)"

clean:
	@echo 'Cleaning out interim directory, leaving "raw" untouched'
	rm -rf interim
