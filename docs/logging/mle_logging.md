# The `MLELogger` Class

## Logging made easy :book:

Each Python based experiment is assumed to use a custom logger: The `MLELogger`. This enables the standardization needed to automatically aggregate multiple random runs and to log performance across hyperparameter searches.

## The API :video_game:

```python
from mle_logging import MLELogger

# Instantiate logging to experiment_dir
log = MLELogger(time_to_track = ['num_updates', 'num_epochs'],
                what_to_track = ['train_loss', 'test_loss'],
                experiment_dir = "experiment_dir/",
                model_type = 'torch')

time_tic = {'num_updates': 10,
            'num_epochs': 1}
stats_tic = {'train_loss': 0.1234,
             'test_loss': 0.1235}

# Update the log with collected data & save it to .hdf5
log.update(time_tic, stats_tic)
log.save()

# Save a model (torch, sklearn, jax, numpy)
log.save_model(model)

# Save a matplotlib figure as .png
fig, ax = plt.subplots()
log.save_plot(fig)

# You can also save (somewhat) arbitrary objects .pkl
some_dict = {"hi" : "there"}
log.save_extra(some_dict)

# Or do everything in one go
log.update(time_tic, stats_tic,
           model, fig, extra,
           save=True)
```

## Generated File Structure :books:

The `MLELogger` will create a nested directory, which looks as follows:

```
experiment_dir
├── extra: Stores saved .pkl object files
├── figures: Stores saved .png figures
├── logs: Stores .hdf5 log files (meta, stats, time)
├── models: Stores different model checkpoints
    ├── final: Stores most recent checkpoint
    ├── every_k: Stores every k-th checkpoint provided in update
    ├── top_k: Stores portfolio of top-k checkpoints based on performance
├── tboards: Stores tensorboards for model checkpointing
├── <config_name>.json: Copy of configuration file (if provided)
```
