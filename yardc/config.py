import os
import yaml

def _load_config(filepath):
    with open(filepath, 'r') as config_file:
        data = yaml.load(config_file.read())
    return data

def _get_filepath():
    return os.path.normpath(
        os.path.join(
            os.path.expanduser("~"),
            '.config',
            'yardc',
            'yardc.yaml'
        )
    )

config = _load_config(_get_filepath())
