# The Future of the Toolbox

You can find a couple things that need to be tackled in the [issues of this project](https://github.com/RobertTLange/mle-toolbox/issues). Below is a quick overview of large milestones that could need your help:

- [ ] Make `mle init` beautiful/a smoother/more minimal experience.
- [ ] Better documentation via sphinx, code style and PEP setup.
- [ ] Automated env/container generation + clean up (delete if existing)
- [ ] Asynchronous job scheduling based on "trigger event".
- [ ] Core functionalities for Population-based training.
    - [ ] Exploit Strategies
    - [ ] Explore Strategies
    - [ ] `PBT_Manager`
- [ ] Multi-objective SMBO (pareto front improvements).
    - [ ] Based BOTorch with different acquisition functions.
    - [ ] Make `BaseHyperOptimisation` more general/adaptive.
    - [ ] Get rid of `scikit-optimize` unstable dependency.
- [ ] Modular adding of remote cloud VM backends:
    - [ ] Google Cloud Platform VM instances
    - [ ] Amazon Web Services
    - [ ] Microsoft Azure
- [ ] `mle-labortaory` Web UI/Server.
    - [ ] Based on streamlit
    - [ ] Monitoring from everywhere with password protection
    - [ ] Easy retrieval of results via click
    - [ ] Easy report generation via click
    - [ ] Launch experiments from UI interface
- [ ] More tests in test suite for core features of toolbox.
    - [ ] Update existing integration tests
    - [ ] Test the MLE_Logger
    - [ ] Test log merging
