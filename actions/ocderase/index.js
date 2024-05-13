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
            console.error(`ERROR: ${error.message}`);
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
                        console.log(logOut);
                    }
                    console.log(`Process exited with code ${code} -- OK`);
                    resolve(0);
                } else {
                    console.log(logOut);
                    console.log(`Process exited with code ${code}`);
                    reject(code);
                }
            } else {
                console.log(logOut);
                console.log(`Process exited with code ${code}`);
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
    let cfgMax32xxx = await fileExists(path.join(env.OPENOCD_PATH, 'target', 'max32xxx.cfg'));
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
    for (let i = 0; i < BOARD_IDS.length; i++) {
        if (cfgMax32xxx) {
            target = 'MAX32xxx';
        } else {
            target = targets[i]
        }
        promises[i] = eraseFlash(
            target, 0, dapSNs[i], gdbPorts[0], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
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
        if (retCodes[i] === 0) {
            if (cfgMax32xxx) {
                target = 'MAX32xxx';
            } else {
                target = targets[i]
            }
            await eraseFlash(
                targets[i], 1, dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
            ).then(
                (success) => procSuccess(success, 'Erase'),
                (error) => procFail(error, 'Erase', false)
            );
        }
    }
}

main();
