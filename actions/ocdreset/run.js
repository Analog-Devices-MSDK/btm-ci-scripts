const Core = require('@actions/core');
const Github = require('@actions/github');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');

const BOARD_IDS = Core.getMultilineInput('board');
const OWNER_REF = Github.context.ref;

const resetBoard = function(target, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', 'init; reset; exit'
    ];
    let logOut = '';
    return new Promise((resolve, reject) => {
        const resetCmd = spawn('openocd', args);
        resetCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        resetCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        resetCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        resetCmd.on('close', code => {
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
    let owner = await getBoardOwner(BOARD_IDS);
    const targets = [];
    const dapSNs = [];
    const gdbPorts = [];
    const tclPorts = [];
    const telnetPorts = [];
    let promises = [];
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
        promises[i] = resetBoard(
            targets[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i]
        ).catch(
            (error) => procFail(error, 'Reset', false)
        )
    }
    await Promise.all(promises).then(
        (values) => {
            for (const val of values) {
                procSuccess(val, 'Reset');
            }
        }
    );
}

main();
