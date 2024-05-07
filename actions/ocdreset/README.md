# OCD Reset Action

This action resets a board using openOCD. Both single or multiple boards are accepted as input.

## Inputs

### board

**Required** The ID or the board or boards to reset. ID must match on present in either the `boards_config.json` file or in a custom board configuration JSON.

### suppress_output

Flag used to indicate that console stdout data should be suppressed. Console stderr, error, and exit data will still be printed. Default: `"false"`.


## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/ocdreset@main
with:
  board: |
    max32655_board1
    max32655_board2
  suppress_output: true
```