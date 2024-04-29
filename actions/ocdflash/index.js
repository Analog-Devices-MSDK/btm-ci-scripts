const Core = require('@actions/core');
const Github = require('@actions/github');
const path = require('path');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');
const { makeProject } = require('../make-project');

const BOARD_IDS = Core.getMultilineInput('board');
const PROJECT_DIRS = Core.getMultilineInput('project');
const MSDK_PATH = Core.getInput('msdk_path', { required: false });
const BUILD_FLAG = Core.getBooleanInput('build', { required: false });
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required : false });
const OWNER_REF = Github.context.ref;

const flashBoard = function (target, elf, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `program ${elf} verify; reset; exit`
    ];
    let logOut = '';
    return new Promise((resolve, reject) => {
        const flashCmd = spawn('openocd', args);
        flashCmd.stdout.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        flashCmd.stderr.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        flashCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        flashCmd.on('close', code => {
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
    if (PROJECT_DIRS.length === 1 && BOARD_IDS.length > 1) {
        for (let i = 0; i < BOARD_IDS.length; i++) {
            PROJECT_DIRS[i] = PROJECT_DIRS[0];
        }
    } else if (PROJECT_DIRS.length !== BOARD_IDS.length) {
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
    const elfPaths = [];

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
        let projPath = path.join(MSDK_PATH, 'Examples', targets[i], 'Bluetooth', PROJECT_DIRS[i]);
        elfPaths[i] = path.join(projPath, 'build', `${targets[i].toLowerCase()}.elf`);
        if (BUILD_FLAG) {   
            await makeProject(projPath, DISTCLEAN_FLAG);
        }
    }
    let promises = [];
    for (let i = 0; i < BOARD_IDS.length; i++) {
        promises[i] = flashBoard(
            targets[i], elfPaths[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i]
        ).catch((err) => procFail(err, 'Flash', true));
    }
    let retCodes = await Promise.all(promises).then(
        (values) => {
            for (const val of values) {
                procSuccess(val, 'Flash');
            }
        }
    );
    for (const i in retCodes) {
        if (retCodes[i] != 0) {
            await flashBoard(
                targets[i], elfPaths[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i]
            ).then(
                (success) => procSuccess(success, 'Flash'),
                (error) => procFail(error, 'Flash', false)
            );
        }
    }
}

main();
