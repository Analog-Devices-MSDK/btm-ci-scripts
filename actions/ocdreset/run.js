const Core = require('@actions/core');
const Github = require('@actions/github');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');

const BOARD_ID = Core.getInput('board');
const OWNER_REF = Github.context.ref;

const resetBoard = function(target, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', 'init; reset; exit'
    ];
    return new Promise((resolve, reject) => {
        const resetCmd = spawn('openocd', args);
        resetCmd.stdout.on('data', data => { console.log(data.toString().trim()) });
        resetCmd.stderr.on('data', data => { console.log(data.toString().trim()) });
        resetCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        resetCmd.on('close', code => {
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
        await resetBoard(target, dapSN, gdbPort, tclPort, telnetPort).then(
            (success) => { return procSuccess(success, 'Reset'); },
            (error) => { return procFail(error, 'Reset', false); }
        )
    } else {
        console.log("!! ERROR: Improper permissions. Board could not be reset. !!");
    }
}

main();
