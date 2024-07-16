import os
import shutil
import subprocess


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
