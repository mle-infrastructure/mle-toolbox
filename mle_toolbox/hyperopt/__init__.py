try:
    import skopt
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `scikit-optimize` "
                              "to use the `mle_toolbox.hyperopt` module.")

from .hyperopt_logger import HyperoptLogger
from .random_hyperopt import RandomHyperoptimisation
from .grid_hyperopt import GridHyperoptimisation
from .smbo_hyperopt import SMBOHyperoptimisation

__all__ = [
           'HyperoptLogger',
           'RandomHyperoptimisation',
           'GridHyperoptimisation',
           'SMBOHyperoptimisation'
           ]
