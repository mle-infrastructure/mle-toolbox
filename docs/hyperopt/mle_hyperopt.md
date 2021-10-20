# The `mle-hyperopt` Package

## Hyperoptimization made easy :rocket:

All hyperparameter search experiments are based on the `mle-hyperopt` package. It is a standalone package and can easily be used independently of the `mle-toolbox`. For a quickstart checkout the [notebook blog](https://github.com/RobertTLange/mle-hyperopt/blob/main/examples/getting_started.ipynb).

## The API 🎮

```python
from mle_hyperopt import RandomSearch

configs = strategy.ask(batch_size=1)
values = [train_network(c) for c in configs]
strategy.tell(configs, values)
from mle_hyperopt import RandomSearch

# Instantiate random search class
strategy = RandomSearch(real={"lrate": {"begin": 0.1,
                                        "end": 0.5}},
                        integer={"batch_size": {"begin": 32,
                                                "end": 128,
                                                "spacing": 32}},
                        categorical={"arch": ["mlp", "cnn"]})

# Simple ask - eval - tell API
configs = strategy.ask(5)
values = [train_network(**c) for c in configs]
strategy.tell(configs, values)
```

|     | Search Types           | Description | `search_config` |
| --- |----------------------- | ----------- | --------------- |
| 📄  |  `GridSearch`          |  Grid search  over list of discrete values  | - |
| 📄  |  `RandomSearch`        |  Random search over variable ranges         | `refine_after`, `refine_top_k` |
| 📄  |  `SMBOSearch`          |  Sequential model-based optimization        | `base_estimator`, `acq_function`, `n_initial_points`
| 📄  |  `CoordinateSearch`    |  Coordinate-wise optimization with defaults | `order`, `defaults`
| 📄  |  `NevergradSearch`     |  Multi-objective wrapper for [nevergrad](https://facebookresearch.github.io/nevergrad/) | `optimizer`, `budget_size`, `num_workers`


## Installation ⏳

A PyPI installation is available via:

```
pip install mle-hyperopt
```

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/RobertTLange/mle-hyperopt.git
cd mle-hyperopt
pip install -e .
```

## Further Options 🚴

### Saving & Reloading Logs 🏪

```python
# Storing & reloading of results from .pkl
strategy.save("search_log.pkl")
strategy = RandomSearch(..., reload_path="search_log.pkl")

# Or manually add info after class instantiation
strategy = RandomSearch(...)
strategy.load("search_log.pkl")
```

### Search Decorator 🧶

```python
from mle_hyperopt import hyperopt

@hyperopt(strategy_type="grid",
          num_search_iters=25,
          real={"x": {"begin": 0., "end": 0.5, "bins": 5},
                "y": {"begin": 0, "end": 0.5, "bins": 5}})
def circle_objective(config):
    distance = abs((config["x"] ** 2 + config["y"] ** 2))
    return distance

strategy = circle_objective()
strategy.log
```

### Storing Configuration Files 📑


```python
# Store 2 proposed configurations - eval_0.yaml, eval_1.yaml
strategy.ask(2, store=True)
```

### Retrieving Top Performers & Visualizing Results 📉

```python
# Get the top k best configurations
# Retrieving the best performing configuration
strategy.get_best(top_k=4)
```
