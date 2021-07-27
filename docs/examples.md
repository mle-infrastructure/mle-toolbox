# Examples :school_satchel:

For all example experiments you can add several command line options:

- `--no_welcome`: Don't print welcome messages at experiment launch.
- `--no_protocol`: Do not record experiment in protocol database.
- `--resource_to_run local`: Run the experiment locally on your machine.

* :page_facing_up: [Euler PDE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/numpy_pde) - Integrate a PDE using forward Euler for different initial conditions.

```
mle run numpy_pde/pde_single.yaml             # Run single .json configuration  
mle run numpy_pde/pde_configs.yaml            # Run two configs for 10 seeds each
mle run numpy_pde/pde_search_grid.yaml        # Run synchronous gridsearch over 2 variables
mle run numpy_pde/pde_search_grid_async.yaml  # Run asynchronous gridsearch over 2 variables
mle run numpy_pde/pde_search_random.yaml      # Run random search over 2 variables
mle run numpy_pde/pde_search_smbo.yaml        # Run sequential model-based optimization
```

### :page_facing_up: [MNIST CNN](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/torch_mnist) - Train Torch CNNs on multiple random seeds & different training configs.

```
mle run torch_mnist/mnist_pre_post.yaml       # Run one config with separate pre-/post-processing
mle run torch_mnist/mnist_configs.yaml        # Run two configs for 10 seeds each
mle run torch_mnist/mnist_search.yaml         # Run synchronous gridsearch over 2 variables
```

* :page_facing_up: [JAX VAE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/jax_vae) - Search through the hyperparameter space of a MNIST VAE.

```
mle run jax_vae/vae_search.yaml               # Run synchronous gridsearch over the learning rate
```

* :page_facing_up: [Sklearn SVM](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/sklearn_svm) - Train a SVM classifier to classify low-dimensional digits.

```
mle run sklearn_svm/svm_single.yaml           # Run single .json configuration
```

* :page_facing_up: [Multi Bash](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/bash_configs) - Launch multi-configuration experiments for bash based jobs.

```
mle run bash_configs/bash_configs.yaml        # Run two configs for 5 seeds each
```

* :page_facing_up: [MNIST PBT](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/pbt_mnist) - Population-Based Training for a MNIST MLP network.

```
mle run pbt_mnist/mnist_pbt.yaml              # Run Population-Based Training on Lrate
```

# Notebooks :pencil:

- :notebook: [Evaluate Results](notebooks/evaluate_results.ipynb) - Walk through post-processing pipeline (loading/visualization).
- :notebook: [Hypothesis Testing](notebooks/hypothesis_testing.ipynb) - Compare different experiment runs & perform hypothesis tests.
- :notebook: [GIF Animations](notebooks/animate_results.ipynb) - Walk through set of animation helpers.
- :notebook: [PBT Evaluation](notebooks/inspect_pbt.ipynb) - Visualize and inspect the result from Population-Based Training.
