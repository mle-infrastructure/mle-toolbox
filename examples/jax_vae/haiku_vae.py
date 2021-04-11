import haiku as hk
import jax
import jax.numpy as jnp
import numpy as np
import optax
import tensorflow_datasets as tfds
from typing import NamedTuple
from mle_toolbox import MLExperiment

# Adapted from dm-haiku example:
# https://github.com/deepmind/dm-haiku/blob/master/examples/vae.py

def load_dataset(split, batch_size):
    ds = tfds.load("binarized_mnist", split=split, shuffle_files=True)
    ds = ds.shuffle(buffer_size=10 * batch_size)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(buffer_size=5)
    ds = ds.repeat()
    return iter(tfds.as_numpy(ds))


class Encoder(hk.Module):
    """Encoder model."""
    def __init__(self, hidden_size = 512, latent_size = 10):
        super().__init__()
        self._hidden_size = hidden_size
        self._latent_size = latent_size

    def __call__(self, x):
        x = hk.Flatten()(x)
        x = hk.Linear(self._hidden_size)(x)
        x = jax.nn.relu(x)
        mean = hk.Linear(self._latent_size)(x)
        log_stddev = hk.Linear(self._latent_size)(x)
        stddev = jnp.exp(log_stddev)
        return mean, stddev


class Decoder(hk.Module):
    """Decoder model."""
    def __init__(self, hidden_size = 512, output_shape = (28, 28, 1)):
        super().__init__()
        self._hidden_size = hidden_size
        self._output_shape = output_shape

    def __call__(self, z):
        z = hk.Linear(self._hidden_size)(z)
        z = jax.nn.relu(z)
        logits = hk.Linear(np.prod(self._output_shape))(z)
        logits = jnp.reshape(logits, (-1, *self._output_shape))
        return logits


class VAEOutput(NamedTuple):
    image: jnp.ndarray
    mean: jnp.ndarray
    stddev: jnp.ndarray
    logits: jnp.ndarray


class VariationalAutoEncoder(hk.Module):
    """Main VAE model class, uses Encoder & Decoder under the hood."""
    def __init__(self, hidden_size = 512, latent_size = 10,
               output_shape = (28, 28, 1)):
        super().__init__()
        self._hidden_size = hidden_size
        self._latent_size = latent_size
        self._output_shape = output_shape

    def __call__(self, x):
        x = x.astype(jnp.float32)
        mean, stddev = Encoder(self._hidden_size, self._latent_size)(x)
        z = mean + stddev * jax.random.normal(hk.next_rng_key(), mean.shape)
        logits = Decoder(self._hidden_size, self._output_shape)(z)
        p = jax.nn.sigmoid(logits)
        image = jax.random.bernoulli(hk.next_rng_key(), p)
        return VAEOutput(image, mean, stddev, logits)


def binary_cross_entropy(x, logits):
    if x.shape != logits.shape:
        raise ValueError("inputs x and logits must be of the same shape")
    x = jnp.reshape(x, (x.shape[0], -1))
    logits = jnp.reshape(logits, (logits.shape[0], -1))
    return -jnp.sum(x * logits - jnp.logaddexp(0.0, logits), axis=-1)


def kl_gaussian(mean: jnp.ndarray, var: jnp.ndarray) -> jnp.ndarray:
    return 0.5 * jnp.sum(-jnp.log(var) - 1.0 + var + mean**2, axis=-1)


def main(mle):
    model = hk.transform(lambda x: VariationalAutoEncoder()(x))
    optimizer = optax.adam(mle.train_config.l_rate)

    @jax.jit
    def loss_fn(params, rng_key, batch):
        """ELBO loss: E_p[log(x)] - KL(d||q), where p ~ Be(0.5), q ~ N(0,1)."""
        outputs: VAEOutput = model.apply(params, rng_key, batch["image"])
        log_likelihood = -binary_cross_entropy(batch["image"], outputs.logits)
        kl = kl_gaussian(outputs.mean, outputs.stddev**2)
        elbo = log_likelihood - kl
        return -jnp.mean(elbo)

    @jax.jit
    def update(params, rng_key, opt_state, batch):
        """Single SGD update step."""
        grads = jax.grad(loss_fn)(params, rng_key, batch)
        updates, new_opt_state = optimizer.update(grads, opt_state)
        new_params = optax.apply_updates(params, updates)
        return new_params, new_opt_state

    rng_seq = hk.PRNGSequence(mle.train_config.seed_id)
    params = model.init(next(rng_seq), np.zeros((1, *(28, 28, 1))))
    opt_state = optimizer.init(params)

    train_ds = load_dataset(tfds.Split.TRAIN, mle.train_config.batch_size)
    valid_ds = load_dataset(tfds.Split.TEST, mle.train_config.batch_size)

    for step in range(mle.train_config.training_steps):
        params, opt_state = update(params, next(rng_seq), opt_state, next(train_ds))

        if step % mle.train_config.eval_freq == 0:
            val_loss = loss_fn(params, next(rng_seq), next(valid_ds))
            # Log the results to the logger
            time_tic = {"step_counter": step}
            stats_tic = {"val_loss": float(val_loss)}
            mle.update_log(time_tic, stats_tic,
                           model=params, save=True)


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
