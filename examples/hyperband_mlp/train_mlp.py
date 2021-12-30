from mle_toolbox import MLExperiment
import torch
import math


def main(mle):
    """Train 3rd order polynomial to approx sin(x) on -pi to pi. Following:
    github.com/pytorch/tutorials/blob/master/beginner_source/examples_nn/polynomial_nn.py"""
    x = torch.linspace(-math.pi, math.pi, 2000)
    y = torch.sin(x)
    p = torch.tensor([1, 2, 3])
    xx = x.unsqueeze(-1).pow(p)

    model = torch.nn.Sequential(torch.nn.Linear(3, 1), torch.nn.Flatten(0, 1))

    # Reload model checkpoint if provided in config SH/PBT cases
    if mle.model_ckpt is not None:
        model.load_state_dict(mle.model_ckpt)

    loss_fn = torch.nn.MSELoss()

    if "sh_num_add_iters" in mle.train_config.extra.keys():
        num_gd_steps = (
            mle.train_config.extra.sh_num_add_iters * mle.train_config.gd_steps_per_iter
        )
    else:
        num_gd_steps = 50

    for t in range(num_gd_steps):
        y_pred = model(xx)
        loss = loss_fn(y_pred, y)

        model.zero_grad()
        loss.backward()
        with torch.no_grad():
            for param in model.parameters():
                param -= float(mle.train_config.params.lrate) * param.grad

        mle.log.update(
            {"num_steps": t},
            {"loss": loss.item()},
            model=model,
            save=True,
        )


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
