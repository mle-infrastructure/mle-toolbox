try:
    import statsmodels
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `statsmodels` "
                              "to use the `mle_toolbox.hypothesis` module.")


from .hypothesis_tester import HypothesisTester


__all__ = [
           "HypothesisTester",
          ]
