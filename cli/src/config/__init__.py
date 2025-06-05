import os
import yaml
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"
print(config_path)

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

if not config:
    config = {}

def store_config(config: dict) -> None:
    with open(config_path, "w") as f:
        yaml.dump(config, f)

def set_config(key: str, value: str) -> None:
    config[key] = value
    store_config(config)
    
def set_default_config() -> None:
    if not config.get("EMULATOR_ANDROID_VERSION"):
        config["EMULATOR_ANDROID_VERSION"] = os.getenv("EMULATOR_ANDROID_VERSION") 
    if not config.get("EMULATOR_IMG_TYPE"):
        config["EMULATOR_IMG_TYPE"] = os.getenv("EMULATOR_IMG_TYPE") 
    if not config.get("EMULATOR_SYS_IMG"):
        config["EMULATOR_SYS_IMG"] = os.getenv("EMULATOR_SYS_IMG") 
    if not config.get("EMULATOR_DEVICE"):
        config["EMULATOR_DEVICE"] = os.getenv("EMULATOR_DEVICE") 
    
    config["EMULATOR_DATA_PARTITION"] = os.getenv("EMULATOR_DATA_PARTITION") 
    config["EMULATOR_ADDITIONAL_ARGS"] = os.getenv("EMULATOR_ADDITIONAL_ARGS") 
    config["EMULATOR_NAME"] = os.getenv("EMULATOR_NAME") 
    config["EMULATOR_NO_SKIN"] = os.getenv("EMULATOR_NO_SKIN") 
    config["EMULATOR_CONFIG_PATH"] = os.getenv("EMULATOR_CONFIG_PATH") 

set_default_config()
__all__ = ["config", "store_config", "set_config"]