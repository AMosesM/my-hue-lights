PROD_NAME=my-hue-lights-prod
VENV_NAME=my-hue-lights-venv

PROD_CONTAINER_ID=$(shell docker ps -a | grep $(PROD_NAME) | awk '{ print $$1 }' )
VENV_CONTAINER_ID=$(shell docker ps -a | grep $(VENV_NAME) | awk '{ print $$1 }' )

PROD_IMAGE_ID=$(shell docker image ls -a | grep $(PROD_NAME) | awk '{ print $$1 }' )
VENV_IMAGE_ID=$(shell docker image ls -a | grep $(VENV_NAME) | awk '{ print $$1 }' )

VENV_PREPPED_IMAGE_ID=$(shell docker image ls -a | grep $(VENV_NAME)-prepped | awk '{ print $$1 }' )


.PHONY venv-prep:
venv-prep:
ifeq (${VENV_PREPPED_IMAGE_ID},)
	docker build -f Dockerfile.venv -t $(VENV_NAME) .
	docker run -t -d --name $(VENV_NAME) $(VENV_NAME)
	docker exec -it $(VENV_NAME) python /opt/app/setup_bridges.py
	docker commit $(VENV_NAME) $(VENV_NAME)-prepped
	docker stop $(VENV_NAME)
	docker container rm $(VENV_NAME)
	docker image rm $(VENV_NAME)
endif

.PHONY build:
build: venv-prep
	docker build -f Dockerfile.app -t $(PROD_NAME) .

.PHONY run:
run:
	docker run -p 5000:5000 --name $(PROD_NAME) $(PROD_NAME)

.PHONY run-detach:
run-detach:
	docker run --detach -p 5000:5000 --name $(PROD_NAME) --restart unless-stopped $(PROD_NAME)

.PHONY start:
start:
	docker start ${PROD_CONTAINER_ID}

.PHONY stop-prod:
stop-prod:
ifneq (${PROD_CONTAINER_ID},)
	docker stop ${PROD_CONTAINER_ID}
endif

.PHONY stop-venv:
stop-venv:
ifneq (${VENV_CONTAINER_ID},)
	docker stop ${VENV_CONTAINER_ID}
endif

.PHONY clean:
clean: clean-venv clean-prod

.PHONY clean-prod:
clean-prod: stop-prod
ifneq (${PROD_CONTAINER_ID},)
	docker container rm $(PROD_CONTAINER_ID)
endif

ifneq (${PROD_IMAGE_ID},)
	docker image rm $(PROD_IMAGE_ID)
endif

.PHONY clean-venv:
clean-venv: stop-venv
ifneq (${VENV_CONTAINER_ID},)
	docker container rm $(VENV_CONTAINER_ID)
endif
ifneq (${VENV_IMAGE_ID},)
	docker image rm $(VENV_IMAGE_ID)
endif

.PHONY list:
list:
	docker image ls
	docker container ls
.PHONY list-all:
list-all:
	docker image ls -a
	docker container ls -a

.PHONY: reload-run
reload-run: clean-prod build run

.PHONY: reload-run-detach
reload-run-detach: clean-prod build run-detach
