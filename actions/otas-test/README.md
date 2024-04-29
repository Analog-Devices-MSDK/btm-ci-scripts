# OTAS Test Action

This action runs the OTAS test on the indicated boards.

## Inputs

### board_client

**Required** ID of the board that should act as the client. ID must match a target present in either the `boards_config.json` file or in a custom board configuration JSON.

### board_server

**Required** ID of the board that should act as the server. ID must match a target present in either the `boards_config.json` file or in a custom board configuration JSON.

### msdk_path

Path to the root directory of the local MSDK. Default: `'.'`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/otas-test@main
with:
  board_client: max32655_board1
  board_server: max32655_board2
  msdk_path: msdk
```