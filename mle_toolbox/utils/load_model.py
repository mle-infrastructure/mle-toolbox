from .core_files_load import load_pkl_object


def load_model(ckpt_path: str, model_type: str, model=None):
    """ Helper to reload stored checkpoint/pkl & return trained model. """
    if model_type == "torch":
        try:
            import torch
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(f"{err}. You need to install "
                                      "`torch` if you want to save a model "
                                      "checkpoint.")
        if model is None:
            raise ValueError("Please provide a torch model instance.")
        checkpoint = torch.load(ckpt_path, map_location='cpu')
        model.load_state_dict(checkpoint)
    elif model_type in ["jax", "sklearn"]:
        model = load_pkl_object(ckpt_path)
    return model
