import os
import shutil
import subprocess
from resource_manager import ResourceManager


def create_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        shutil.rmtree(directory)
        os.mkdir(directory)


def dict_to_table(data: dict):
    table = []

    for key, value in data.items():
        if isinstance(value, float):
            table.append[key, round(value, 2)]
        else:
            table.append[key, value]


def get_git_hash(path):
    try:
        return (
            subprocess.run(["git", "-C", f"{path}", "rev-parse", "HEAD"])
            .stdout.decode("ascii")
            .strip()
        )
    except:
        return "Unknown"


def make_version_table():
    return [
        ["Repo", "Git Hash"],
        ["MSDK", get_git_hash(os.getenv("MAXIM_PATH"))],
        ["RF-PHY", get_git_hash(os.getenv("RF_PHY_PATH"))],
    ]


def config_switches(resource_manager: ResourceManager, slave: str, master: str):
    """Configure RF switches to connect DUTS

    Parameters
    ----------
    resource_manager : ResourceManager
        resource manager to access switch information
    slave : str
        slave resource
    master : str
        slave_resource
    """
    slave_sw_model, slave_sw_port = resource_manager.get_switch_config(slave)
    master_sw_model, master_sw_port = resource_manager.get_switch_config(master)

    assert (
        slave_sw_model and slave_sw_port
    ), "Slave must have the sw_model and sw_state attribute"
    assert (
        master_sw_model and master_sw_port
    ), "Master must have the sw_model and sw_state attribute"
    assert (
        slave_sw_model != master_sw_model
    ), "Boards must be on opposite switches to connect!"

    with mc_rf_sw.MiniCircuitsRFSwitch(model=slave_sw_model) as sw_slave:
        print("Configuring Slave Switch")
        sw_slave.set_sw_state(slave_sw_port)

    with mc_rf_sw.MiniCircuitsRFSwitch(model=master_sw_model) as sw_master:
        print("Configuring Master Switch")
        sw_master.set_sw_state(master_sw_port)
