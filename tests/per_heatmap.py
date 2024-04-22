import sys
sys.path.append("..")
sys.path.append("/home/btm-ci/Tools/msdk-ble-test-suite/src")
import subprocess
import argparse
import json
import os
from Resource_Share.resource_manager import ResourceManager
from ble_test_suite_v2.phy import rx_sensitivity as rx_sens
from ble_test_suite_v2.controllers import RxSensitivityTestController

def flash_board(msdk: str, project: str, board_id: str) -> int:
    rm = ResourceManager()
    target = rm.get_item_value(f"{board_id}.target")
    board = rm.get_item_value(f"{board_id}.board")
    build_path = os.path.join(msdk, "Examples", target, "Bluetooth", project)
    proc = subprocess.Popen(["make", f"MAXIM_PATH={msdk}", "distclean"], cwd=build_path)
    if proc.wait() != 0:
        print("!! ERROR CLEANING DIRECTORY, ABORTING !!")
        return -1
    proc = subprocess.Popen(
        ["make", "-j8", f"MAXIM_PATH={msdk}", f"TARGET={target}", f"BOARD={board}"], cwd=build_path)
    if proc.wait() != 0:
        print("!! ERROR BUILDING PROJECT, ABORTING !!")
        return -1
    elf_path = os.path.join(build_path, "build", f"{target.lower()}.elf")
    proc = subprocess.Popen(["bash", "-c", f"ocdflash {board_id} {elf_path}"])
    if proc.wait() != 0:
        print("!! ERROR FLASHING, ERASING AND RETRYING 1 TIME !!")
        proc = subprocess.Popen(["bash", "-c", f"ocderase {board_id}"])
        if proc.wait() != 0:
            print("!! MASS ERASE FAILED, ABORTING !!")
            return -1
        proc = subprocess.Popen(["bash", "-c", f"ocdflash {board_id} {elf_path}"])
        if proc.wait() != 0:
            print("!! ERROR FLASHING, ABORTING !!")
            return -1
    return 0

if __name__ == '__main__':
    DESC = "Generate PER heatmaps"
    parser = argparse.ArgumentParser(
        description=DESC, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("msdk", type=str, help="MSDK path.")
    parser.add_argument("dut_target", type=str, help="DUT board type.")
    parser.add_argument("master_target", type=str, help="Master board type.")
    parser.add_argument("group", type=str, help="DUT/master group field.")
    parser.add_argument("results_dir", type=str, help="Base results path.")
    parser.add_argument(
        "--long", action="store_true",
        help="Run full sweep. Default is to run a spot check."
    )

    args = parser.parse_args()
    if args.long:
        # cfg_path = os.environ.get("PER_CFG_FULLSWEEP")
        cfg_path = "rx_sensitivity_config.json"
    else:
        # cfg_path = os.environ.get("PER_CFG_SPOTCHECK")
        cfg_path = "rx_sensitivity_config.json"
    group = args.group.upper()
    dut_target = args.dut_target.upper()
    master_target = args.master_target.upper()
    rm = ResourceManager()
    dut = rm.get_applicable_items(target=dut_target, group=group)[0]
    rm.lock_resource(dut)
    master = rm.get_applicable_items(target=master_target, group=group)[0]
    rm.lock_resource(master)
    print(dut)
    print(master)

    with open(cfg_path, "r", encoding="utf-8") as cfile:
        cfg = json.load(cfile)
        cfg["config"]["equipment"] = {
            "dut" : dut_target,
            "dut_port" : rm.get_item_value(f"{dut}.hci_port"),
            "master" : master_target,
            "master_port" : rm.get_item_value(f"{master}.hci_port")
        }
        cfg["config"]["paths"]["results_dir"]  = os.path.join(
            args.results_dir,
            f"{dut_target.upper()}"
        )
        
    with open(cfg_path, "w", encoding="utf-8") as cfile:
        cfile.write(json.dumps(cfg, indent=4))

    if flash_board(args.msdk, "BLE5_ctr", dut) != 0:
        rm.unlock_resources([dut, master])
        sys.exit(-1)

    ctrl = RxSensitivityTestController(rx_sens.init_from_json(cfg_path))
    ctrl.run_test()
    passes = ctrl.results()

    if not passes:
        print("!! DUT FAILED ON ONE OR MORE SWEEPS !!")
        rm.unlock_resources([dut, master])
        sys.exit(-1)

    rm.unlock_resources([dut, master])
    sys.exit(0)
