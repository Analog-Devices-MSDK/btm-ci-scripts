# OCD Erash Action

This action erases the flash on a board using openOCD. Both a single board or multiple boards are accepted as input.

## Inputs

### board

**Required** The ID of the board or boards to erase. ID must match one present in either the `boards_config.json` file or in a custom board configuration JSON.

### suppress_output

Flag used to indicate that console stdout data should be suppressed. Console stderr, error, and exit data will still be printed. Default: `"false"`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/ocderase@main
with:
  board: |
    max32665_board1
    max32690_board_w1
  has_two_flash_banks: true
  suppress_output: true
```