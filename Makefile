.PHONY: install lint mypy test coverage pycln black isort clean pre-commit run-debug run-prod run-schedule run-schedule-tasks run-async-tasks build

define HELP_MESSAGE
make help:
	print help message
make install:
	setup local develop environment
make lint:
	check code style
make mypy:
	code static check
make test:
	run all test cases
make coverage:
	statistics code coverage
make pycln:
	help to remove useless import
make black:
	help to format code style
make isort:
	help to sort import segment
make clean:
	remove files/dirs in .gitignore
make pre-commit:
	run pre-commit hooks
make run-api-debug:
	run debug api server
	params:
		PORT port
		WORKERS worker number
	exapmle: make PORT=9100 run-api-debug
make run-api-prod:
	run production api server
	params:
		PORT port
		WORKERS worker number
	exapmle: make PORT=9100 WORKERS=1 run-api-prod
make run-grpc-debug:
	run debug grpc server
	params:
		PORT port
		WORKERS worker number
	exapmle: make PORT=9100 run-grpc-debug
make run-grpc-prod:
	run production grpc server
	params:
		PORT port
		WORKERS worker number
	exapmle: make PORT=9100 WORKERS=1 run-grpc-prod
make check-grpc-health:
	run grpc health check
	params:
		PORT port
		WORKERS worker number
make run-schedule:
	start celery beat
make run-schedule-tasks:
	start celery worker to deal with schedule tasks
make run-async-tasks:
	start celery worker to deal with async tasks
make build:
	build docker image
	params:
		TAG image tag
	exapmle: make TAG=1.0 build
endef

PROJECT_NAME:=jingdong_financial
PORT ?= 8080
WORKERS ?= 8
# image tag
TAG ?= 1.0
.DEFAULT: help
help:
	$(info $(HELP_MESSAGE))
	@echo
# install prod env
install:
	conda env create -f environment.yaml

# init dev env
install-dev:
	conda env create -f environment.yaml
	conda activate jingdong_financial
	pre-commit install

# update env
update:
	conda env update -f environment.yaml

lint:
	pre-commit run -v pylint --all-files

mypy:
	pre-commit run -v mypy --all-files

test:
	pytest -s -v .

coverage:
	pytest --cov=infra --cov=. tests --cov-report html

pycln:
	pre-commit run -v pycln --all-files

black:
	pre-commit run -v black --all-files

isort:
	pre-commit run -v isort --all-files

clean:
	git clean -Xdf

pre-commit:
	pre-commit run -v --all-files

run-api-debug:
	python manager.py run-api-server

run-api-prod-uvicorn:
	uvicorn api_server.fastapi_app:app --workers $(WORKERS) --host 0.0.0.0 --port $(PORT) --no-access-log

run-api-prod:
	gunicorn api_server.fastapi_app:app  -c api_server/gunicorn.conf.py

run-schedule:
	python manager.py run-schedule

run-schedule-tasks:
	python manager.py run-schedule-tasks

run-async-tasks:
	python manager.py run-async-tasks

# build docker image
build:
	docker build -f docker/Dockerfile -t $(PROJECT_NAME):$(TAG) .
