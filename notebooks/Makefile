.PHONY: image run-notebook clean 

JOVYAN_USER=jovyan
JOVYAN_HOME=/home/$(JOVYAN_USER)/
NOTEBOOK_PATH=$(PWD)/notebook
DEFAULT_CONTAINER_NAME:=video_reuse_detector_notebook
TAG:=$(DEFAULT_CONTAINER_NAME)
IMAGE:=$(DEFAULT_CONTAINER_NAME)

define RUN_NOTEBOOK
-@docker rm -f $(CONTAINER_NAME) 2> /dev/null
@docker run -d -p $(PORT):8888 \
		--name $(CONTAINER_NAME) \
		-v $(PWD):$(JOVYAN_HOME) \
		$(DOCKER_ARGS) \
		$(IMAGE) bash -c "$(PRE_CMD) chown $(JOVYAN_USER) $(JOVYAN_HOME) && start-notebook.sh $(ARGS)" > /dev/null
endef

image: DOCKER_ARGS?=
image:
	@docker build --rm $(DOCKER_ARGS) -t $(TAG) .

run-notebook: PORT?=80
run-notebook: CONTAINER_NAME?=$(DEFAULT_CONTAINER_NAME)
run-notebook:
	$(RUN_NOTEBOOK)

clean: CONTAINER_NAME?=$(DEFAULT_CONTAINER_NAME)
clean:
	@docker rm -f $(CONTAINER_NAME)
