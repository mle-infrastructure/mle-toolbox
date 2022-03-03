install:
	# Install minimal requirements
	python -m pip install --upgrade pip
	pip install -r requirements/requirements.txt
	pip install -e .

install-dev:
	# Install requirements for testing/development
	python -m pip install --upgrade pip
	pip install -r requirements/requirements.txt
	pip install -r requirements/requirements-test.txt
	pip install git+https://github.com/mle-infrastructure/mle-logging.git@main
	pip install git+https://github.com/mle-infrastructure/mle-hyperopt.git@main
	pip install git+https://github.com/mle-infrastructure/mle-launcher.git@main
	pip install git+https://github.com/mle-infrastructure/mle-monitor.git@main
	pip install pytest pytest-timeout pytest-cov
	pip install flake8 black pydocstyle
	pip install -e .

clean:
	# Remove all python installation dependencies
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf .pytype/
	rm -rf dist/

format:
	# Run hard formatting with PEP8 style
	black --verbose ./mle_toolbox

lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 ./mle_toolbox --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 ./mle_toolbox --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

docstrings:
	# Check compliance with Python docstring conventions - PEP257.
	pydocstyle

type-check:
	# Run type-checking
	# mypy mle_toolbox/.

testing:
	# Run unit tests: File loading, job template generation
	# pytest -vv --durations=0 --cov=./ --cov-report=term-missing --cov-report=xml tests/unit
	# Run integration tests: Different experiment types [ignore report test]
	# pytest -vv --durations=0 --cov=./ --cov-report=term-missing --cov-report=xml tests/integration/experiment
	pytest -vv --durations=0 --cov=./ --cov-report=term-missing --cov-report=xml --ignore=tests/integration/test_pbt_api.py

pypi-publish:
	# Publish package in PyPi repositories - triggered for new release
	python -m pip install --upgrade pip
	pip install setuptools wheel twine
	python setup.py sdist bdist_wheel
	twine upload dist/*
