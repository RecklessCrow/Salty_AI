import json


def create_run_config(model_name, gambler, user):
    """
    This function creates a run configuration object.
    :return: run_config
    """
    run_config = {
        "user": user,
        "gambler": type(gambler).__name__,
    }

    with open(f"/opt/saltybet/saved_models/{model_name}/run_config.json", "w") as f:
        json.dump(run_config, f)
