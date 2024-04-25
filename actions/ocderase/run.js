const Core = require('@actions/core');
const Github = require('@actions/github');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');

const BOARD_ID = Core.getInput('board');
const HAS_TWO_FLASH_BANKS = Core.getBooleanInput('has_two_flash_banks', { required: false });
const OWNER_REF = Github.context.ref;

const eraseFlash = function(target, bank, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `init; reset halt; max32xxx mass_erase ${bank}; exit`
    ];
    return new Promise((resolve, reject) => {
        const eraseCmd = spawn('openocd', args);
        eraseCmd.stdout.on('data', (data) => { console.log(data.toString().trim()) });
        eraseCmd.stderr.on('data', (data) => { console.log(data.toString().trim()) });
        eraseCmd.on('error', (error) => {
            console.error(`ERROR: ${error.message}`);
        });
        eraseCmd.on('close', (code) => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const main = async function () {
    let owner = await getBoardOwner(BOARD_ID);
    if (owner === OWNER_REF) {
        let target = await getBoardData(BOARD_ID, 'target');
        let dapSN = await getBoardData(BOARD_ID, 'dap_sn');
        let gdbPort = await getBoardData(BOARD_ID, 'ocdports.gdb');
        let tclPort = await getBoardData(BOARD_ID, 'ocdports.tcl');
        let telnetPort = await getBoardData(BOARD_ID, 'ocdports.telnet');
        let bank = 0;

        let retCode = await eraseFlash(target, bank, dapSN, gdbPort, tclPort, telnetPort).then(
            (success) => { return procSuccess(success, 'Erase'); },
            (error) => { return procFail(error, 'Erase', false); }
        )
        if (retCode == 0) {
            if (HAS_TWO_FLASH_BANKS) {
                bank = 1;
                await eraseFlash(target, bank, dapSN, gdbPort, tclPort, telnetPort).then(
                    (success) => { return procSuccess(success, 'Erase'); },
                    (error) => { return procFail(error, 'Erase', false); }
                );
            }
        }
    } else {
        console.log("!! ERROR: Improper permissions. Board could not be erased. !!");
    }
}

main();
