# OCD Flash Action

This action flashes a given project to a board using openOCD. Optionally, the action can build the project prior to flashing. Both a single board/project or multiple board/projects are accepted as input. If multiple boards are supplied, the number of project folders supplied must either be 1 or equal to the number of boards.

## Inputs

### board

**Required** The ID of the board or boards to flash. ID must match one present in either the `boards_config.json` file or in a custom board configuration JSON.

### project

**Required** The name of the project that should be flashed to the board. This should be a singular folder name as opposed to a full path. For example: `BLE5_ctr` as opposed to `msdk/Examples/MAX32655/Bluetooth/BLE5_ctr`.

### msdk_path

Path to the root directory of the local MSDK. Default: `'.'`.

### build

Flag used to indicate that the project should be built before it is flashed. Default: `"false"`.

### distclean

Flag used to indicate that a distclean should be performed prior to building the project. If `build` is false, this input is ignored. Default: `"False"`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/ocdflash@main
with:
  board: |
    max32655_board1
    max32655_board2
  project: |
    BLE_datc
    BLE_dats
  msdk_path: msdk
  build: true
  distclean: true
```