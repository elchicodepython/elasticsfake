from os import environ
from yaml import safe_load
from infra.confdict import DottyConfDict


def configure_confdict():
    """Load configuration dictionary from a YAML file specified by an environment variable.

    The function checks for the 'CONFIG_FILE_PATH' environment variable to get the path of the
    configuration file. If the variable is not set, it raises an EnvironmentError. It then reads
    the YAML file and loads its contents into a Dotty dictionary for easy access to nested keys.

    Returns:
        dotty: A Dotty dictionary containing the configuration settings.

    Raises:
        EnvironmentError: If 'CONFIG_FILE_PATH' is not set in the environment variables.
        FileNotFoundError: If the specified configuration file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """

    config_file_path = environ.get("CONFIG_FILE_PATH")
    if not config_file_path:
        raise EnvironmentError("Environment variable 'CONFIG_FILE_PATH' is not set.")

    with open(config_file_path, "r") as file:
        config_data = safe_load(file)

    return DottyConfDict(config_data)
