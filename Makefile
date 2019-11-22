SHELL=/bin/bash

# This wizardry comes from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Makes "make" call "make help" by default
.DEFAULT_GOAL := help

init: ## Installs python dependencies for local development. Please install ffmpeg manually
	@echo 'Install python dependencies'
	pip3 install pipenv
	pipenv --python python3.7
	pipenv install --dev

.PHONY: installcheck
installcheck: ## Checks that dependencies are installed, if everything is okay nothing is outputted
	@which docker-compose > /dev/null || (echo "ERROR: docker-compose not found"; exit 1)

.env:
	@touch $@
	@echo "REACT_APP_API_URL=http://localhost:5001" >> $@

opencv: .env
	@if [[ ! -d "$@" ]]; then\
		git clone https://github.com/opencv/opencv.git --depth=1 $@;\
	fi

    # Check if the path to the samples have already been added,
    # otherwise add it in
	grep -qxF 'OPEN_CV_SAMPLES=$(CURDIR)/$@/samples/data' .env || echo 'OPEN_CV_SAMPLES=$(CURDIR)/$@/samples/data' >> .env

.PHONY: jslint
jslint: ## Run lint checks for React-application
	docker-compose exec frontend npm run lint

.PHONY: jslint-fix
jslint-fix: ## Run lint checks for React-application and attempt to automatically fix them
	docker-compose exec frontend npm run lint:fix

.PHONY: flake8
flake8:  ## Run lint checks for Python-code
	docker-compose exec middleware flake8 .

.PHONY: autoflake
autoflake: ## Run autoflake to remove unused imports and variables
	docker-compose exec middleware autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive middleware
	docker cp video_reuse_detector_middleware_1:/usr/src/app/tests .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/middleware .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/video_reuse_detector .

.PHONY: lint
lint: black-check flake8 isort-check jslint ## Run lint checks for Python-code and the React application

.PHONY: mypy
mypy: ## Run type-checks for Python-code
	docker-compose exec middleware mypy . --ignore-missing-imports

.PHONY: doctest
doctest: ## Execute doctests for Python-code
	docker-compose exec middleware python -m doctest -v video_reuse_detector/*.py

.PHONY: pyunittest
pyunittest: opencv ## Execute Python-unittests. Note, this does not run the video_reuse_detector tests in a docker container as it won't have sufficient memory
	pipenv run python -m unittest discover -s tests
	docker-compose exec middleware python -m unittest discover -s middleware/tests

.PHONY: black-check
black-check: ## Dry-run the black-formatter on Python-code with the --check option, doesn't normalize single-quotes
	docker-compose exec middleware black . -S --check --exclude=video_reuse_detector/orb.py

.PHONY: black-diff
black-diff: ## Dry-run the black-formatter on Python-code with the --diff option, doesn't normalize single-quotes
	docker-compose exec middleware black . -S --diff --exclude=video_reuse_detector/orb.py

.PHONY: black-fix
black-fix: ## Run the black-formatter on Python-code, doesn't normalize single-quotes. This will change the code if "make black-check" yields a non-zero result
	docker-compose exec middleware black . -S --exclude=video_reuse_detector/orb.py
	docker cp video_reuse_detector_middleware_1:/usr/src/app/tests .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/middleware .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/video_reuse_detector .

.PHONY: isort
isort-check: ## Dry-run isort on the Python-code, checking the order of imports
	docker-compose exec middleware isort --check-only

.PHONY: isort-fix
isort-fix: ## Run isort on the Python-code, checking the order of imports. This will change the code if "make isort" yields a non-empty result
	docker-compose exec middleware isort
	docker cp video_reuse_detector_middleware_1:/usr/src/app/tests .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/middleware .
	docker cp video_reuse_detector_middleware_1:/usr/src/app/video_reuse_detector .

test: doctest mypy pyunittest

.PHONY: check
check: lint test

.PHONY: build-images
build-images: installcheck ## Builds the docker images
	docker-compose build

.PHONY: run-containers
run-containers: build-images ## Run the docker images
	docker-compose up -d

up: ## Alias for "run-containers" to allow for "make down && make build && make up" chaining
	@make run-containers

.PHONY: recreate-db
recreate-db: run-containers ## Recreate the database, nuking the contents therein
	docker-compose exec middleware python -m middleware.manage recreate_db

.PHONY: stop
stop: ## Stop the containers
	docker-compose stop

.PHONY: down
down: ## Bring down the containers
	docker-compose down

.PHONY: forcebuild
forcebuild: ## Forces a rebuild, ignoring cached layers
	docker-compose build --no-cache 

.PHONY: remove-images
remove-images: ## Forcefully remove _all_ docker images
	docker rmi $(docker images -q)

.PHONY: connect-to-db
connect-to-db: ## Access database through psql. Use \c video_reuse_detector_dev or \c video_reuse_detector_test to connect to either database. Use \dt to describe the tables
	docker-compose exec db psql -U postgres

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
