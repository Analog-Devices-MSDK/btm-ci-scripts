# Find Board Action

This action finds and returns the ID or a board which matches the given criteria. Both single or multiple sets of criteria are accepted as input. If multiple sets of criteria are given, the length of the groups field and the length of the target field must either be equal to each other, or one of the two lengths must be equal to 1.

## Inputs

### target

**Required** Desired part number or numbers. Must match a target present in either the `boards_config.json` file or in a custom board configuration JSON.

### group

**Required** Desired test group or groups. Must match a group present in either the `boards_config.json` file or in a custom board configuration JSON.

### num_boards

If multiple boards are required with the same criteria, the number of boards can be indicated here instead of providing the criteria above multiple times. If the length of either the `target` or the `group` value is greater than 1, this value is ignored. Default: `'1'`.


## Outputs

### board[n]

Board matching the given criteria, where `n` is from 1...10 and matches the position of the criteria in the original input.

## Example usage

```yaml
- name: Fetch Boards
  id: findBoards
  uses: Analog-Devices-MSDK/btm-ci-scripts/actions/find-board@main
  with:
    target: MAX32655
    group: APP
    num_boards: 2
```

The output can be accessed via `${{ steps.STEPID.outputs.OUTPUTNAME}}. In this case:

```yaml
- name: Echo Output
  run: echo "Found matching boards --> ${{ steps.findBoards.outputs.board1 }}, ${{ steps.findBoards.outputs.board2 }}"
```

Console output:

```
Found matching boards --> max32655_board1, max32655_board2
```