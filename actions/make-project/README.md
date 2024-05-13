# Make Project Action

This action builds a project using make. Optionally, a distclean can be performed prior to building. If no distclean is indicated, a basic clean will still be performed. Only a single project can be accepted as input at a time.

## Inputs

### path

Path to the project that should be built. Default: `'.'`.

### distclean

Flag used to indicated that a distclean should be performed instead of a normal clean. Default: `'false'`.

### build_flags

Additional flags to use if building. Default: `""`.

### suppress_output

Flag used to indicate that console stdout data should be suppressed. Console stderr, error, and exit data will still be printed. Default: `"false"`.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/make-project@main
with:
  path: msdk/Examples/MAX32655/Bluetooth/BLE5_ctr
  distclean: true
  suppress_output: true
```
