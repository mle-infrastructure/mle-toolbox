

class ExplorationStrategy(object):
    def __init__(self, exploration_type):
        """ Exploration Strategies for PBT (Jaderberg et al. 17). """
        self.exploration_type = exploration_type

    def perturb(self):
        """ Multiply hyperparam independently by random factor of 0.8/1.2. """

    def resample(self):
        """ Resample hyperparam from original prior distribution. """

    def explore(self):
        return
