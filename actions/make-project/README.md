# Make Project Action

This action builds a project using make. Optionally, a distclean can be performed prior to building. If no distclean is indicated, a basic clean will still be performed. Only a single project can be accepted as input at a time.

## Inputs

### project

Path to the project that should be built or the project directory name. Default: `'.'`.

### targets

Targets to build projects for, only required if a full project path is not provided. Default: `""`.

### msdk_path

Path to MSDK installation, only required if a full project path is not provided. Default: `"."`.

### distclean

Flag used to indicated that a distclean should be performed instead of a normal clean. Default: `'false'`.

### build_flags

Additional flags to use when building and/or cleaning. Default: `""`.

### suppress_output

Flag used to indicate that console stdout data should be suppressed. Console stderr, error, and exit data will still be printed. Default: `"false"`.

### create_buildlog

Flag used to indicate that build command output should be echoed to a logfile. Default: `"false"`.

## Outputs

### log_directory

If flag is set, the path to the directory in which logfiles were saved.

## Example usage

```yaml
uses: Analog-Devices-MSDK/btm-ci-scripts/actions/make-project@main
id: buildProject
with:
  project: BLE5_ctr
  target: MAX32655
  msdk_path: ${{ github.workspace }}
  distclean: true
  buildflags: 'clean.cordio'
  create_buildlog: true
```

The output can be accessed via `${{ steps.STEPID.outputs.OUTPUTNAME }}`. In this case:

```yaml
- name: Echo Output
  run: |
    echo "Logfile directory --> ${{ steps.buildProject.outputs.log_directory }}"
    ls ${{ steps.buildProject.outputs.log_directory }}
```
