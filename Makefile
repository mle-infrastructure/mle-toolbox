install:
	python -m pip install --upgrade pip
	pip install -r requirements/requirements.txt
	pip install -e .

install-dev:
	python -m pip install --upgrade pip
	pip install -r requirements/requirements.txt
	pip install -r requirements/requirements-test.txt
	pip install pytest pytest-timeout flake8
	pip install -e .

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf .pytype/
	rm -rf dist/
	rm -rf docs/_build

formatter:
	black --verbose ./mle_toolbox

lint:
	# stop the build if there are Python syntax errors or undefined names
	flake8 ./mle_toolbox --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 ./mle_toolbox --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

types:
	mypy mle_toolbox/.

test-unit:
	pytest -vv --durations=0 ./tests/unit

test-integration:
	pytest -vv --durations=0 ./tests/integration
