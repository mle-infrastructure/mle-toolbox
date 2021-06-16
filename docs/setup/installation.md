# Installation

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective cluster resource (Slurm/SGE).

## PyPI Installation

```
pip install mle-toolbox
```

## GitHub Installation

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/RobertTLange/mle-toolbox.git
cd mle-toolbox
pip install -e .
```

By default this will only install the minimal dependencies (not including specialized packages such as `scikit-optimize`, `statsmodels`, etc.). To get all requirements for tests or examples you will need to install [additional requirements](requirements/).

## TODO

### Conda Installation

```
conda install mle-toolbox
```

### Containerization

#### Docker

```
docker run...
```

#### Singularity
