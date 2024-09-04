const Core = require('@actions/core');
const Github = require('@actions/github');
const path = require('path');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail, fileExists, findTargetDirectory } = require('../common');
const { makeProject } = require('../make-project');
const { Cipher } = require('crypto');

const BOARD_IDS = Core.getMultilineInput('boards');
const PROJECT_DIRS = Core.getMultilineInput('project');
const MSDK_PATH = Core.getInput('msdk_path', { required: false });
const BUILD_FLAG = Core.getBooleanInput('build', { required: false });
const BUILD_FLAGS = Core.getMultilineInput('build_flags', { required: false });
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });
const SUPPRESS_FLAG = Core.getBooleanInput('suppress_output', { required: false });
let tmp = Core.getInput('owner', {required: false }); 
const OWNER_REF = tmp ? tmp : Github.context.ref;

const flashBoard = function (target, elf, dap, gdb, tcl, telnet, suppress) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `program ${elf} verify; reset; exit`
    ];
    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        const flashCmd = spawn('openocd', args);
        if (suppress) {
            flashCmd.stdout.on('data', (data) => { dumpOut = `${dumpOut}${data.toString()}` });
            flashCmd.stderr.on('data', (data) => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            flashCmd.stdout.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
            flashCmd.stderr.on('data', (data) => { logOut = `${logOut}${data.toString()}` });
        }
        flashCmd.on('error', error => {
            if (suppress) {
                logOut = `${logOut}${dumpOut}`
            }
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        flashCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            resolve(code);
        });
    });
}

const main = async function () {
    let build_flags = [];

    for (var i=0; i<BUILD_FLAGS.length; i++) {
        build_flags.push(...BUILD_FLAGS[i].split(" "))
    }
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
    const app_boards = []
    retVal = 0;
    for (let i = 0; i < BOARD_IDS.length; i++) {
        let owner = await getBoardOwner(BOARD_IDS[i]);
        if (owner !== OWNER_REF && owner !== undefined) {
            throw new Error(
                `!! ERROR: Improper permissions. Board could not be flashed. !! Owner found ${owner} Expected ${OWNER_REF}, Board ${BOARD_IDS[i]}`
            );
        }
        [targets[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], app_boards[i]] = await Promise.all([
            getBoardData(BOARD_IDS[i], 'target'),
            getBoardData(BOARD_IDS[i], 'dap_sn'),
            getBoardData(BOARD_IDS[i], 'ocdports.gdb'),
            getBoardData(BOARD_IDS[i], 'ocdports.tcl'),
            getBoardData(BOARD_IDS[i], 'ocdports.telnet'),
            getBoardData(BOARD_IDS[i], 'board')
        ]).catch((err) => console.error(err));

        let projPath = findTargetDirectory(path.join(MSDK_PATH, 'Examples', targets[i]), PROJECT_DIRS[i])
        let app_board = app_boards[i] 
        elfPaths[i] = path.join(projPath, 'build', `${targets[i].toLowerCase()}.elf`);
        if (BUILD_FLAG) {   
            await makeProject(projPath, DISTCLEAN_FLAG, build_flags, board=app_board, suppress=SUPPRESS_FLAG).then(
                (success) => procSuccess(success, 'Build'),
                (error) => {
                    retVal--;
                    procFail(error, 'Build', false);
                    Core.setFailed(`Build ${projPath} failed.`);
                }
            );
        }
        if (retVal < 0) {
            return;
        }
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
        promises[i] = flashBoard(
            target, elfPaths[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
        ).catch((err) => procFail(err, 'Flash', false));
    }
    let retCodes = await Promise.all(promises);
    for (let i = 0; i < retCodes.length; i++) {
        if (retCodes[i] != 0) {
            cfgBoardSpec = await fileExists(
                path.join(env.OPENOCD_PATH, 'target', `${targets[i].toLowerCase()}.cfg`));
            if (cfgBoardSpec) {
                target = targets[i];
            } else {
                target = 'MAX32XXX'
            }
            procFail(retCodes[i], 'Flash', true);
            await flashBoard(
                target, elfPaths[i], dapSNs[i], gdbPorts[i], tclPorts[i], telnetPorts[i], SUPPRESS_FLAG
            ).then(
                (value) => {
                    if (value === 0) {
                        procSuccess(success, 'Flash');
                    } else {
                        retVal--;
                        procFail(value, 'Flash', false);
                        Core.setFailed(`Failed to flash ${targets[i]}`);
                    }
                },
                (error) => {
                    retVal--;
                    procFail(error, 'Flash', false);
                    Core.setFailed(`Failed to flash ${targets[i]}.`);
                }
            );
        } else {
            procSuccess(retCodes[i], 'Flash');
        }
        if (retVal < 0) {
            return;
        }
    }
}

main();
