const Core = require('@actions/core');
const Github = require('@actions/github');
const {
    PythonShell
} = require('python-shell');
const {
    spawn
} = require('child_process');
const {
    env
} = require('node:process');
const path = require('path');

const BOARD_ID = Core.getInput('board');
const PROJECT_DIR = Core.getInput('project');
const MSDK_PATH = Core.getInput('msdk_path', {
    required: false
});
const BUILD_FLAG = Core.getBooleanInput('build', {
    required: false
});
const OWNER_REF = Github.context.ref;

const getBoardData = function(boardId, itemName) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../Resource_Share',
        args: [`-g ${boardId}.${itemName}`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_manager.py', options, function(err, results) {
            if (err) reject(err);
            else {
                console.log('%s --> %s', itemName, results[0]);
                resolve(results[0]);
            }
        });
    });
}

const getBoardOwner = function(boardId) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../Resource_Share',
        args: [`--get-owner ${boardId}`]
    }
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

const makeProject = function(projectPath) {
    return new Promise((reject, resolve) => {
        const makeCmd = spawn('make', ['-j', projectPath]);
        makeCmd.stdout.on('data', data => {
            console.log(data)
        });
        makeCmd.stderr.on('data', data => {
            console.log(data)
        });
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

const flashBoard = function(target, elf, dap, gdb, tcl, telnet) {
    const args = [
        `-s ${env.OPENOCD_PATH}`, '-f interface/cmsis-dap.cfg',
        `-f target/${target.toLowerCase()}`, `-c "adapter serial ${dap}"`,
        `-c "gdb_port ${gdb}"`, `-c "telnet_port ${telnet}"`, `-c "tcl_port ${tcl}"`,
        `-c "program ${elf} verify; reset; exit"`
    ];
    return new Promise((reject, resolve) => {
        const flashCmd = spawn('openocd', args);
        flashCmd.stdout.on('data', data => {
            console.log(data)
        });
        flashCmd.stderr.on('data', data => {
            console.log(data)
        });
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

const flashSuccessful = function(val) {
    console.log('Flash Successful');
    return val;
}

const flashAborted = function(val) {
    console.log('!! ERROR: Flash failed. Aborting !!');
    return val;
}

const flashFailed = function(val) {
    console.log('!! ERROR: Flash failed. Retrying 1 time. !!');
    return val;
}

const main = async function() {
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

        retCode = flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
            flashSuccessful,
            flashFailed
        );
        if (retCode != 0) {
            flashBoard(target, elfPath, dapSN, gdbPort, tclPort, telnetPort).then(
                flashSuccessful,
                flashAborted
            );
        }
    } else {
        console.log("!! ERROR: Improper permissions. Board could not be flashed. !!");
    }
}

main();