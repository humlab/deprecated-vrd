.PHONY: help init lint mypy doctest unittest test segment downsample demo clean

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

.env:
	@touch .env

opencv: .env
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

process: FILENAME=$(basename $(notdir $(INPUT_FILE)))
process: SEGMENTS_TXT=$(FILENAME)-segments.txt
process: FRAMES_TXT=$(FILENAME)-frames.txt
process: KEYFRAMES_TXT=$(FILENAME)-keyframes.txt
process: AUDIO_TXT=$(FILENAME)-audio.txt
process: PROCESSED_DIR=processed
process: SOURCES=$(FILENAME)-sources.txt
process: TARGETS=$(FILENAME)-targets.txt
process: interim
	@echo "Processing $(FILENAME)"

	@echo "Producing segments from $(FILENAME), output in $(SEGMENTS_TXT)"
	@make --no-print-directory segment INPUT_FILE="$(INPUT_FILE)" > $(SEGMENTS_TXT)

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
	@sed 's/interim/$(PROCESSED_DIR)/' $(SOURCES) > $(TARGETS)
	./transfer_interim.sh "$(SOURCES)" "$(TARGETS)"

run:
	@echo "Comparing $(QUERY_VIDEO) to $(REFERENCE_VIDEO)"
	pipenv run python -m video_reuse_detector.main $(QUERY_VIDEO) $(REFERENCE_VIDEO)

audio: TARGET_DIRECTORY=$(dir $(INPUT_FILE))
audio: interim
	@echo "Extracting audio from $(INPUT_FILE). Expect output at $(TARGET_DIRECTORY)"
	@pipenv run python -m video_reuse_detector.extract_audio "$(INPUT_FILE)"

clean:
	@echo 'Cleaning out log and txt files'
	rm -rf *.log
	rm -rf *.txt
