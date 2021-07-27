# Installation

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective cluster resource (Slurm/SGE).

## PyPI Installation

The latest release of the toolbox can be installed via [PyPi](https://pypi.org/project/mle-toolbox/):

```
pip install mle-toolbox
```

## GitHub Installation

If you want the most recent version with all pre-release commits, you can clone the repository and afterwards 'manually' install it:

```
git clone https://github.com/RobertTLange/mle-toolbox.git
cd mle-toolbox
pip install -e .
```

By default this will only install the minimal dependencies (not including special packages for hyperparameter optimization such as `scikit-optimize`, `statsmodels`, etc.). To get all requirements for tests or examples you will need to install [additional requirements](requirements/):

```
pip install -r requirements/requirements-test.txt
```

## :fire: Future Support

In the future I plan to add an installation via `conda-forge` and Docker/Singularity images for the `mle-toolbox`.

#### Conda Installation

```
conda install mle-toolbox
```

#### Docker Image

```
docker run...
```

#### Singularity Image

```
singularity pull docker://RobertTLange/...
```
