# mle run - Experiment Execution

An experiment can be launched from the command line via:

```
mle run <experiment_config>.yaml
```

You can add several command line options, which can come in handy when debugging or if you want to launch multiple experiments sequentially:

- `--no_welcome`: Don't print welcome messages at experiment launch.
- `--no_protocol`: Do not record experiment in the PickleDB protocol database.
- `--resource_to_run <resource>`: Run the experiment on the specified resource.

In the following we walk through the different types of supported experiments and show how to provide the necessary configuration specifications.
