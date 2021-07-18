# Population-Based Training

*Note*: This page and content is still work in progress!

```yaml
# Parameters specific to the population-based training
pbt_args:
    pbt_logging:
        max_objective: False
        eval_metric: "test_loss"
    pbt_resources:
        num_population_members: 10
        num_total_update_steps: 2000
        num_steps_until_ready: 500
        num_steps_until_eval: 100
    pbt_config:
        pbt_params:
            real:
                l_rate:
                    begin: 1e-5
                    end: 1e-2
        exploration:
            strategy: "perturb"
        selection:
            strategy: "truncation"
```
