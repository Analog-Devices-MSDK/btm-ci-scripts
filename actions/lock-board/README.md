# Lock Board Action

This action locks/unlocks test boards. Optionally, the timeout for the lock process can be set. Both single or multiple boards are accepted as input.

## Inputs

### boards

**Required** The ID or the board or boards to lock/unlock. ID must match one present in either the `boards_config.json` file or in a custom board configuration JSON.

### lock

Flag used to indicated that a board should be locked. If `false` the board will be unlocked. Default: `'true'`.

### timeout

Timeout for the locking process in seconds. Default: `'1800'`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/lock-board@main
with:
  boards: |
    max32655_board1
    max32655_board2
  lock: true
  timeout: 3600
```