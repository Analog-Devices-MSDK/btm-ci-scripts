const Core = require('@actions/core');
const Github = require('@actions/github');
const path = require('path');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail, fileExists } = require('../common');

const BOARD_IDS = Core.getMultilineInput('board');
const SUPPRESS_FLAG = Core.getBooleanInput('suppress_output', { required: false });
const OWNER_REF = Github.context.ref;

const eraseFlash = function(target, bank, dap, gdb, tcl, telnet, suppress) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `init; reset halt; max32xxx mass_erase ${bank}; exit`
    ];
    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        const eraseCmd = spawn('openocd', args);
        if (suppress) {
            eraseCmd.stdout.on('data', (data) => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            eraseCmd.stdout.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        }
        eraseCmd.stderr.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        eraseCmd.on('error', (error) => {
            // console.error(`ERROR: ${error.message}`);
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        eraseCmd.on('close', (code) => {
            if (code != 0) {
                let logLines = logOut.split(/\r?\n/)
                let idx = logLines.length - 1;
                while (!logLines[idx]) {
                    idx--;
                }
                if (logLines[idx].trim() === 'Error: flash bank 1 does not exist') {
                    if (!suppress) {
                        logOut = `${logOut}Process exited with code ${code} -- OK`
                        console.log(logOut);
                    }
                    console.log(`Process exited with code ${code} -- OK`);
                    resolve(0);
                } else {
                    logOut = `${logOut}Process exited with code ${code}`
                    console.log(logOut);
                    // console.log(`Process exited with code ${code}`);
                    // reject(code);
                    resolve(code);
                }
            } else {
                logOut = `${logOut}Process exited with code ${code}`
                console.log(logOut);
                // console.log(`Process exited with code ${code}`);
                resolve(code);
            }
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
        promises[i] = eraseFlash(
            target, 0, dapSNs[i], gdbPorts[0], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
        ).catch((error) => procFail(error, 'Erase', false));
    }
    let retCodes = await Promise.all(promises).then(
        (values) => {
            for (const val of values) {
                if (val === 0) {
                    procSuccess(val, 'Erase');
                } else {
                    procFail(val, 'Erase', true);
                }
            }
        }
    );
    for (const i in retCodes) {
        if (retCodes[i] === 0) {
            cfgBoardSpec = await fileExists(
                path.join(env.OPENOCD_PATH, 'target', `${targets[i].toLowerCase()}.cfg`));
            if (cfgBoardSpec) {
                target = targets[i];
            } else {
                target = 'MAX32XXX'
            }
            await eraseFlash(
                targets[i], 1, dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
            ).then(
                (value) => {
                    if (value === 0) {
                        procSuccess(success, 'Erase');
                    } else {
                        retVal--;
                        procFail(error, 'Erase', false);
                        Core.setFailed(`Failed to erase ${targets[i]}.`);
                    }
                },
                (error) => {
                    retVal--;
                    procFail(error, 'Erase', false);
                    Core.setFailed(`Failed to erase ${targets[i]}.`);
                }
            );
        }
    }
}

main();
