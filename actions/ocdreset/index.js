const Core = require('@actions/core');
const Github = require('@actions/github');
const path = require('path');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail, fileExists } = require('../common');

const BOARD_IDS = Core.getMultilineInput('board');
const SUPPRESS_FLAG = Core.getBooleanInput('suppress_output', { required: false });
const OWNER_REF = Github.context.ref;

const resetBoard = function(target, dap, gdb, tcl, telnet, suppress) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', 'init; reset; exit'
    ];
    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        const resetCmd = spawn('openocd', args);
        if (suppress) {
            resetCmd.stdout.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            resetCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        }
        resetCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        resetCmd.on('error', error => {
            // console.error(`ERROR: ${error.message}`);
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        resetCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            // console.log(`Process exited with code ${code}`);
            // if (code != 0) reject(code);
            // else {
            //     resolve(code);
            // }
            resolve(code);
        });
    });
}

const main = async function () {
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
    var target;
    var cfgBoardSpec;
    for (let i = 0; i < BOARD_IDS.length; i++) {
        cfgBoardSpec = await fileExists(
            path.join(env.OPENOCD_PATH, 'target', `${targets[i].toLowerCase()}.cfg`));
        if (cfgBoardSpec) {
            target = targets[i];
        } else {
            target = 'MAX32XXX'
        }
        promises[i] = resetBoard(
            target, dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
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
