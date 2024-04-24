const Core = require('@actions/core');
const Github = require('@actions/github');
const { PythonShell } = require('python-shell');
const { spawn } = require('child_process');
const { resolve } = require('path');

const BOARD_ID = Core.getInput('board');
const OWNER_REF = Github.context.ref;

const getBoardData = function (boardId, itemName) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../Resource_Share',
        args: [`-g ${boardId}.${itemName}`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_managet.py', options, function (err, results) {
            if (err) reject(err);
            else {
                console.log('%s --> %s', itemName, results[0]);
                resolve(results[0]);
            }
        });
    });
}

const getBoardOwner = function (boardId) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../Resource_Share',
        args: [`--get-owner ${boardId}`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_manager.py', options, function(err, results) {
            if (err) reject(err);
            else {
                console.log('owner --> %s', results[0]);
                resolve(results[0]);
            }
        });
    });
}

const resetBoard = function(target, dap, gdb, tcl, telnet) {
    const args = [
        `-s ${OPENOCD_PATH}`, '-f interface/cmsis-dap.cfg',
        `-f target/${target.toLowerCase()}.cfg`, `-c "adapter serial ${dap}"`,
        `-c "gdb_port ${gdb}`, `-c "telnet_port ${telnet}"`, `-c "tcl_port ${tcl}"`,
        '-c "init; reset; exit"'
    ];
    return new Promise((reject, resolve) => {
        const resetCmd = spawn('openocd', args);
        resetCmd.stdout.on('data', data => { console.log(data) });
        resetCmd.stderr.on('data', data => { console.log(data) });
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
