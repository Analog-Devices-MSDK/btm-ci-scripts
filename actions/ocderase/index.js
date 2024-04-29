const Core = require('@actions/core');
const Github = require('@actions/github');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');

const BOARD_IDS = Core.getMultilineInput('board');
const HAS_TWO_FLASH_BANKS = Core.getMultilineInput('has_two_flash_banks', { required: false });
const OWNER_REF = Github.context.ref;

const eraseFlash = function(target, bank, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `init; reset halt; max32xxx mass_erase ${bank}; exit`
    ];
    let logOut = '';
    return new Promise((resolve, reject) => {
        const eraseCmd = spawn('openocd', args);
        eraseCmd.stdout.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        eraseCmd.stderr.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        eraseCmd.on('error', (error) => {
            console.error(`ERROR: ${error.message}`);
        });
        eraseCmd.on('close', (code) => {
            console.log(logOut);
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const main = async function () {
    if (HAS_TWO_FLASH_BANKS.length === 1 && BOARD_IDS.length > 1) {
        for (let i = 0; i < BOARD_IDS.length; i++) {
            HAS_TWO_FLASH_BANKS[i] = HAS_TWO_FLASH_BANKS[0];
        }
    } else if (HAS_TWO_FLASH_BANKS.length !== BOARD_IDS.length) {
        console.log("Length of projects list must be 1 or the same as length of boards list.");
        throw new Error(
            '!! ERROR: Mismatched parameter lengths. Board could not be flashed. !!'
        );
    }
    const targets = [];
    const dapSNs = [];
    const gdbPorts = [];
    const tclPorts = [];
    const telnetPorts = [];

    for (let i = 0; i < BOARD_IDS.length; i++) {
        let owner = await getBoardOwner(BOARD_IDS[i]);
        if (owner !== OWNER_REF && owner !== undefined) {
            throw new Error(
                "!! ERROR: Improper permissions. Board could not be flashed. !!"
            );
        }
        [targets[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i]] = await Promise.all([
            getBoardData(BOARD_IDS[i], 'target'),
            getBoardData(BOARD_IDS[i], 'dap_sn'),
            getBoardData(BOARD_IDS[i], 'ocdports.gdb'),
            getBoardData(BOARD_IDS[i], 'ocdports.tcl'),
            getBoardData(BOARD_IDS[i], 'ocdports.telnet')
        ]).catch((err) => console.error(err));
    }
    let promises = [];
    for (let i = 0; i < BOARD_IDS.length; i++) {
        promises[i] = eraseFlash(
            targets[i], 0, dapSNs[i], gdbPorts[0], tclPorts[i], telnetPorts[i]
        ).catch((error) => procFail(error, 'Erase', false));
    }
    let retCodes = await Promise.all(promises).then(
        (values) => {
            for (const val of values) {
                procSuccess(val, 'Erase');
            }
        }
    );
    for (const i in retCodes) {
        if (retCodes[i] === 0 && HAS_TWO_FLASH_BANKS[i]) {
            await eraseFlash(
                targets[i], 1, dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i]
            ).then(
                (success) => procSuccess(success, 'Erase'),
                (error) => procFail(error, 'Erase', false)
            );
        }
    }
}

main();
