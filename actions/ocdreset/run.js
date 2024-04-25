const Core = require('@actions/core');
const Github = require('@actions/github');
const { PythonShell } = require('python-shell');
const { spawn } = require('child_process');
const { env } = require('node:process');

const BOARD_ID = Core.getInput('board');
const OWNER_REF = Github.context.ref;

const getBoardData = function (boardId, itemName) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['-g', `${boardId}.${itemName}`]
    };
    return new Promise((resolve, reject) => {
        PythonShell.run('resource_manager.py', options).then(
            (item) => { console.log('%s --> %s', itemName, item[0]); resolve(item[0]); },
            (error) => reject(error)
        );
    });
}

const getBoardOwner = function (boardId) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['--get-owner', `${boardId}`]
    };
    return new Promise((resolve, reject) => {
        PythonShell.run('resource_manager.py', options).then(
            (ownerId) => {console.log('owner --> %s', ownerId[0]); resolve(ownerId[0]) },
            (error) => reject(error)
        );
    });
}

const resetBoard = function(target, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `adapter serial ${dap}`,
        '-c', `gdb_port ${gdb}`, '-c', `telnet_port ${telnet}`, '-c', `tcl_port ${tcl}`,
        '-c', 'init; reset; exit'
    ];
    return new Promise((resolve, reject) => {
        const resetCmd = spawn('openocd', args);
        resetCmd.stdout.on('data', data => { console.log(data.toString()) });
        resetCmd.stderr.on('data', data => { console.log(data.toString()) });
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

const resetSuccessful = function (val) {
    console.log('Reset successful.');
    return val;
}
const resetAborted = function (val) {
    console.log('!! ERROR: Reset failed. Aborting. !!');
    return val;
}

const main = async function () {
    let owner = await getBoardOwner(BOARD_ID);

    if (owner === OWNER_REF) {
        let target = await getBoardData(BOARD_ID, 'target');
        let dapSN = await getBoardData(BOARD_ID, 'dap_sn');
        let gdbPort = await getBoardData(BOARD_ID, 'ocdports.gdb');
        let tclPort = await getBoardData(BOARD_ID, 'ocdports.tcl');
        let telnetPort = await getBoardData(BOARD_ID, 'ocdports.telnet');
        resetBoard(target, dapSN, gdbPort, tclPort, telnetPort).then(
            resetSuccessful,
            resetAborted
        );
    } else {
        console.log("!! ERROR: Improper permissions. Board could not be reset. !!");
    }
}

main();
