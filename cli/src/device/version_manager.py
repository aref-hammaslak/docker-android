from logging import config
import os
import re
import subprocess
import logging
from src.constants import DEVICE
from src.constants import ENV
from src.device.emulator import Emulator
from src.helper import run_cmd
from src.app import start_device
from src.config import set_config
from src.config import config as config_manager

logger = logging.getLogger("VersionManager")

# ------------  handlers ------------  
def handle_list_installed():
    installed_avs = get_av_list()
    logger.info(f"Installed Android versions: {installed_avs}")
    return

def handle_install(av:str):
        if av[-2] != '.0':
            av = av + '.0'
        installed_avs = get_av_list()
        if av not in Emulator.API_LEVEL.keys():
            logger.error(f"Android {av} is not supported!")
            return
        if av in installed_avs:
            logger.info(f"Android {av} is already installed!")
            return
        logger.info(f"Downloading Android {av}...")
        cmd = (
            f"sudo sdkmanager --install \"platforms;android-{Emulator.API_LEVEL[av]}\""
            f" \"system-images;android-{Emulator.API_LEVEL[av]};google_apis_playstore;x86_64\""
        )
        logger.info(cmd)
        grant_permission_to_sdk_data()
        result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
        if result.returncode != 0:
            logger.error(f"Failed to install Android {av} {result.stderr}")
            return
        
        logger.info(f"Android {av} is installed!")

def handle_upgrade(av:str):
    if av[-2] != '.0':
            av = av + '.0'
    installed_avs = get_av_list()
    
    if av not in installed_avs:
        logger.error(f"Android {av} is not installed!")
    if av == config_manager.get(ENV.EMULATOR_ANDROID_VERSION):
        logger.info(f"Android {av} is already the current version!")
        return
    try:
        old_device_id = get_emulated_device_ids()[0]
    except IndexError:
        logger.error(f"No emulator is running!")
        device:Emulator = start_device()
        device.wait_until_ready()
        old_device_id = get_emulated_device_ids()[0]

    backup_path = os.path.join(os.getenv(ENV.WORK_PATH), f"backup_emulator_{av}.ab")
    backup_from_device(old_device_id, backup_path)
    stop_device(old_device_id)
    logger.info(f"Upgrading Android {av}...")
    set_config(ENV.EMULATOR_ANDROID_VERSION, av)
    new_device:Emulator = start_device()
    new_device_adb_id = get_emulated_device_ids()[0]
    restore_to_device(new_device_adb_id, backup_path)
    logger.info(f"Android {av} is upgraded!")
    set_status(DEVICE.STATUS_READY)
    new_device.wait_until_ready()
    # move process to background
    os.system(f"nohup {new_device_adb_id} &")
    return

# ------------  backup ------------  
def backup_from_device(device_id:str, backup_path:str):
    cmd = f"adb -s {device_id} backup -all -f {backup_path}"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to backup from device {device_id}: {result.stderr.decode('utf-8')}")
        return
    logger.info(f"Backup from device {device_id} is done!")
    return

def restore_to_device(device_id:str, backup_path:str):
    cmd = f"adb -s {device_id} restore {backup_path}"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to restore to device {device_id}: {result.stderr.decode('utf-8')}")
        return
    logger.info(f"Restore to device {device_id} is done!")
    remove_backup(backup_path)
    return

def remove_backup(backup_path:str):
    cmd = f"rm -rf {backup_path}"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to remove backup {backup_path}: {result.stderr.decode('utf-8')}")
        return

def backup_data_dir(device_id: str, backup_path: str, data_dir: str = "/data/data"):
    cmd = f"adb -s {device_id} pull {data_dir} {backup_path}"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to pull data from device {device_id}: {result.stderr.decode('utf-8')}")
        return
    logger.info(f"Data pulled from device {device_id} to {backup_path}")

def restore_data_dir(device_id: str, backup_path: str, data_dir: str = "/data/data"):
    cmd = f"adb -s {device_id} push {backup_path} {data_dir}"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to push data to device {device_id}: {result.stderr.decode('utf-8')}")
        return
    logger.info(f"Data pushed to device {device_id} from {backup_path}")

# ------------  stop ------------  
def stop_device(adb_id:str):
    cmd = f"adb -s {adb_id} emu kill"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to stop device {adb_id}: {result.stderr.decode('utf-8')}")
        return
    logger.info(f"Device {adb_id} is stopped!")
    return

# ------------  helper functions ------------  
def get_av_list():
    output = run_cmd("sdkmanager --list_installed")
    installed_api = re.findall(f"platforms;android-(\d+)", output)
    installed_api = [int(api[-2:]) for api in installed_api]
    installed_avs = map(lambda x: Emulator.API_LEVEL_REVERSE[str(x)], installed_api)
    return list(installed_avs)

def grant_permission_to_sdk_data():
    cmd = "sudo chown -R $USER /opt/android && sudo chmod -R 774 /opt/android"
    logger.info(cmd)
    result = subprocess.run(cmd, shell=True, stdout=None, stderr=None)
    if result.returncode != 0:
        logger.error(f"Failed to grant permission to sdk data: {result.stderr.decode('utf-8')}")
        return

def get_emulated_device_ids():
    cmd = "adb devices"
    result = run_cmd(cmd, split=True)
    return list(map(lambda x : x.split()[0],result[1:]))

def set_status(current_status:str) -> None:
    bashrc_file = f"{os.getenv(ENV.WORK_PATH)}/device_status"
    with open(bashrc_file, "w+") as bf:
        bf.write(current_status)