const Core = require('@actions/core');
const Github = require('@actions/github');
const { PythonShell } = require('python-shell');
const { spawn } = require('child_process');
const { env } = require('node:process');

const BOARD_ID = Core.getInput('board');
const HAS_TWO_FLASH_BANKS = Core.getBooleanInput('has_two_flash_banks', { required: false });
const OWNER_REF = Github.context.ref;

const getBoardData = function (boardId, itemName) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['-g', `${boardId}.${itemName}`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_manager.py', options, function (err, results) {
            if (err) reject(err);
            else {
                console.log('%s --> %s', itemName, results[0]);
                resolve(results[0]);
            }
        });
    });
}

const getBoardOwner = function (boardId) {
    console.log('HERE')
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['--get-owner', `${boardId}`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_manager.py', options, function (err, results) {
            if (err) reject(err);
            else {
                console.log('owner --> %s', results[0]);
                resolve(results[0]);
            }
        });
    });
}

const eraseFlash = function(target, bank, dap, gdb, tcl, telnet) {
    const args = [
        '-s', `${env.OPENOCD_PATH}`, '-f', 'interface/cmsis-dap.cfg',
        '-f', `target/${target.toLowerCase()}.cfg`, '-c', `"adapter serial ${dap}"`,
        '-c', `"gdb_port ${gdb}"`, '-c', `"telnet_port ${telnet}"`, '-c', `"tcl_port ${tcl}"`,
        '-c', `"init; reset halt; max32xxx mass_erase ${bank}"; exit`
    ];
    return new Promise((reject, resolve) => {
        const eraseCmd = spawn('openocd', args);
        eraseCmd.stdout.on('data', (data) => { console.log(data) });
        eraseCmd.stderr.on('data', (data) => { console.log(data) });
        eraseCmd.on('error', (error) => {
            console.error(`ERROR: ${error.message}`);
        });
        eraseCmd.on('close', (code) => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const eraseSuccessful = function (val) {
     console.log('Erase successful.');
     return val;
}
const eraseAborted = function (val) {
    console.log('!! ERROR: Erase failed. Aborting. !!');
    return val;
}

const main = async function () {
    console.log('starting+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++');
    let owner = await getBoardOwner(BOARD_ID);
    console.log(owner)
    if (owner === OWNER_REF) {
        let target = await getBoardData(BOARD_ID, 'target');
        let dapSN = await getBoardData(BOARD_ID, 'dap_sn');
        let gdbPort = await getBoardData(BOARD_ID, 'ocdports.gdb');
        let tclPort = await getBoardData(BOARD_ID, 'ocdports.tcl');
        let telnetPort = await getBoardData(BOARD_ID, 'ocdports.telnet');
        let flashBank = 0;
        let retCode = eraseFlash(target, flashBank, dapSN, gdbPort, tclPort, telnetPort).then(
            eraseSuccessful,
            eraseAborted
        )
        console.log('============RETCODE --> %s===================', retCode);
        if (retCode == 0) {
            if (HAS_TWO_FLASH_BANKS) {
                flashBank = 1;
                eraseFlash(target, flashBank, dapSN, gdbPort, tclPort, telnetPort).then(
                    eraseSuccessful,
                    eraseAborted
                );
            }
        }

    } else {
        console.log("!! ERROR: Improper permissions. Board could not be erased. !!");
    }
}

main();
