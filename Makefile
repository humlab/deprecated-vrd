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
install-check: ## Checks that dependencies are installed, if everything is okay nothing is outputted
	@which docker-compose > /dev/null || (echo "ERROR: docker-compose not found"; exit 1)
	@which pipenv > /dev/null || (echo "ERROR: pipenv not found"; exit 1)
	@stat "frontend/node_modules/.bin/eslint" > /dev/null || (echo 'Please install ESlint (run npm i inside the \"frontend\"-directory)')

.PHONY: black-check
black-check: ## Dry-run the black-formatter on Python-code with the --check option, doesn't normalize single-quotes
	@echo "Running black with --check"
	@pipenv run black . -S --check --exclude="video_reuse_detector/orb.py|notebooks"

.PHONY: flake8-check
flake8-check:  ## Run lint checks for Python-code
	@echo "Running flake8"
	pipenv run flake8 video_reuse_detector middleware tests

.PHONY: isort-check
isort-check: ## Dry-run isort on the Python-code, checking the order of imports
	@echo "Running isort --check-only"
	@pipenv run isort --skip notebooks --check-only

.PHONY: jslint-check
jslint-check: ## Run lint checks for React-application
	npm run lint --prefix frontend

.PHONY: lint-check
lint-check: black-check flake8-check isort-check jslint-check ## Run lint checks for Python-code and the React application

.PHONY: mypy-check
mypy-check: ## Run type-checks for Python-code
	@echo "Running mypy"
	pipenv run mypy video_reuse_detector tests middleware --ignore-missing-imports

.PHONY: check
check: lint-check mypy-check

.PHONY: autoflake-fix
autoflake-fix: ## Run autoflake to remove unused imports and variables
	@echo "Running autoflake"
	@pipenv run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive --exclude notebooks tests video_reuse_detector middleware

.PHONY: black-fix
black-fix: ## Run the black-formatter on Python-code, doesn't normalize single-quotes. This will change the code if "make black-check" yields a non-zero result
	@echo "Running black"
	@pipenv run black . -S --exclude="video_reuse_detector/orb.py|notebooks"

.PHONY: isort-fix
isort-fix: ## Run isort on the Python-code, checking the order of imports. This will change the code if "make isort" yields a non-empty result
	@echo "Running isort"
	@pipenv run isort --skip notebooks

.PHONY: jslint-fix
jslint-fix: ## Run lint checks for React-application and attempt to automatically fix them
	npm run lint:fix --prefix frontend

fix: autoflake-fix black-fix isort-fix jslint-fix ## Apply lint fixes etcetera.
	@echo "Have a look at these (output may be empty)"
	@git ls-files --others --exclude-standard

.PHONY: doctest
doctest: ## Execute doctests for Python-code
	pipenv run python -m doctest -v video_reuse_detector/*.py

.PHONY: middleware-test
middleware-test:  ## Test the backend
	docker-compose exec middleware python -m unittest discover -s middleware/tests

.PHONY: video_reuse_detector-test
video_reuse_detector-test: ## Execute Python-unittests for core engine. Note, this does not run the video_reuse_detector tests in a docker container as it won't have sufficient memory
	pipenv run python -m unittest discover -s tests

.PHONY: test
test: doctest middleware-test video_reuse_detector-test

.PHONY: black-diff
black-diff: ## Dry-run the black-formatter on Python-code with the --diff option, doesn't normalize single-quotes
	@echo "Running black with --diff"
	@pipenv run black . -S --diff --exclude="video_reuse_detector/orb.py|notebooks"

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
