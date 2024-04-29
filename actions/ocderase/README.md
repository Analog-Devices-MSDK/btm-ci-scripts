# OCD Erash Action

This action erases the flash on a board using openOCD. Both a single board or multiple boards are accepted as input.

## Inputs

### board

**Required** The ID of the board or boards to erase. ID must match one present in either the `boards_config.json` file or in a custom board configuration JSON.

### has_two_flash_banks

Flag used to indicate that at least one of the boards to erase uses two flash banks which should both be erased. Default: `"false"`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/ocderase@main
with:
  board: |
    max32665_board1
    max32690_board_w1
  has_two_flash_banks: true
```