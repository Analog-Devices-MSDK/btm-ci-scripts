const Core = require('@actions/core');
const Github = require('@actions/github');
const path = require('path');
const { spawn } = require('child_process');
const { env } = require('node:process');
const { getBoardData, getBoardOwner, procSuccess, procFail } = require('../common');

const BOARD_ID = Core.getInput('board');
const PROJECT_DIR = Core.getInput('project');
const MSDK_PATH = Core.getInput('msdk_path', { required: false });
const BUILD_FLAG = Core.getBooleanInput('build', { required: false });
const OWNER_REF = Github.context.ref;

const makeProject = function (projectPath) {
    return new Promise((resolve, reject) => {
        const makeCmd = spawn('make', ['-j', '-C', projectPath]);
        makeCmd.stdout.on('data', data => { console.log(data.toString().trim()) });
        makeCmd.stderr.on('data', data => { console.log(data.toString().trim()) });
        makeCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        makeCmd.on('close', code => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        })
    })
}

const flashBoard = function (target, elf, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', `program ${elf} verify; reset; exit`
    ];
    return new Promise((resolve, reject) => {
        const flashCmd = spawn('openocd', args);
        flashCmd.stdout.on('data', data => { console.log(data.toString().trim()) });
        flashCmd.stderr.on('data', data => { console.log(data.toString().trim()) });
        flashCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        flashCmd.on('close', code => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    })
}

// const flashSuccessful = function (val) {
//     console.log('Flash Successful');
//     return val;
// }

// const flashAborted = function (val) {
//     console.log('!! ERROR: Flash failed. Aborting !!');
//     return val;
// }

// const flashFailed = function (val) {
//     console.log('!! ERROR: Flash failed. Retrying 1 time. !!');
//     return val;
// }

const main = async function () {
    let owner = await getBoardOwner(BOARD_ID);

    if (owner === OWNER_REF) {
        let target = await getBoardData(BOARD_ID, 'target');
        let projectPath = path.join(MSDK_PATH, 'Examples', target, 'Bluetooth', PROJECT_DIR)
        if (BUILD_FLAG) {
            await makeProject(projectPath);
        }
        let elfPath = path.join(projectPath, 'build', `${target.toLowerCase()}.elf`);
        let dapSN = await getBoardData(BOARD_ID, 'dap_sn');
        let gdbPort = await getBoardData(BOARD_ID, 'ocdports.gdb');
        let tclPort = await getBoardData(BOARD_ID, 'ocdports.tcl');
        let telnetPort = await getBoardData(BOARD_ID, 'ocdports.telnet');

        // retCode = await flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
        //     flashSuccessful,
        //     flashFailed
        // );
        // if (retCode != 0) {
        //     flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
        //         flashSuccessful,
        //         flashAborted
        //     );
        // }
        retCode = await flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
            (success) => { return procSuccess(success, 'Flash'); },
            (error) => { return procFail(error, 'Flash', true); }
        );
        if (retCode != 0) {
            flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
                (success) => { return procSuccess(success, 'Flash'); },
                (error) => { return procFail(error, 'Flash', false); }
            );
        }
    } else {
        console.log("!! ERROR: Improper permissions. Board could not be flashed. !!");
    }
}

main();
