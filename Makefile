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

.PHONY: video_reuse_detector_test
video_reuse_detector_test: ## Execute Python-unittests for core engine. Note, this does not run the video_reuse_detector tests in a docker container as it won't have sufficient memory
	pipenv run python -m unittest discover -s tests

.PHONY: middleware_test
middleware_test:  ## Test the backend
	docker-compose exec middleware python -m unittest discover -s middleware/tests

.PHONY: pyunittest
pyunittest: video_reuse_detector_test middleware_test

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

fix: ## Apply lint fixes etcetera.
	@echo "Running isort"
	@pipenv run isort --skip notebooks

	@echo "Running black"
	@pipenv run black . -S --exclude="video_reuse_detector/orb.py|notebooks"

	@echo "Running autoflake"
	@pipenv run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive --exclude notebooks tests video_reuse_detector middleware

	@echo "Have a look at these (output may be empty)"
	@git ls-files --others --exclude-standard

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

interim:
	@mkdir $@

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

clean: ## Cleans out artefacts created by the application software. Does not clean docker volumes
	@echo '1. Cleaning out ffreport*.log-files'
	# This line echoes out what the command will do
	@find . -type f -name "ffreport*.log" -exec echo rm -f {} +
	@find . -type f -name "ffreport*.log" -exec rm -f {} +
	
	@echo '2. Cleaning out .txt-files'
	# This line echoes out what the command will do
	@find . -type f -name "*.txt" ! -name "requirements*.txt" ! -name "minimal_archive.txt" ! -name "robots.txt" ! -path "frontend/node_modules" -exec echo rm -f {} +
	@find . -type f -name "*.txt" ! -name "requirements*.txt" ! -name "minimal_uploads.txt" ! -name "robots.txt" ! -path "frontend/node_modules" -exec rm -f {} +


	@echo '3. Cleaning out interim-directories (if nothing is printed after this line, there was nothing to remove)'
	# This line echoes out what the command will do
	@find . -type d -name "interim" -exec echo rm -rf {} +
	@find . -type d -name "interim" -exec sudo rm -rf {} +

	@echo '4. Removing test artefacts'
	@rm -rf static/tests/output

remove_volumes: ## Cleans out docker volumes.
	docker volume rm video_reuse_detector_postgres_data
