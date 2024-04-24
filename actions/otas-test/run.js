const Core = require('@actions/core');
const { PythonShell } = require('python-shell');
const { spawn } = require('child_process');
const path = require('path');

const BOARD_CLIENT = Core.getInput('board_client');
const BOARD_SERVER = Core.getInput('board_server');
const MSDK_PATH = Core.getInput('msdk_path');
const SERVER = 10;
const CLIENT = 20;

const getTarget = function (boardId) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../Resource_Share',
        args: [`-g ${boardId}.target`]
    };
    return new Promise((reject, resolve) => {
        PythonShell.run('resource_manager.py', options, function (err, results) {
            if (err) reject(err);
            else {
                console.log('target --> %s', results[0]);
                resolve(results[0]);
            }
        });
    });
}

const makeProject = function (target, role) {
    let project = (role === SERVER) ? 'BLE_otas' : 'BLE_otac';
    let fullPath = path.join(MSDK_PATH, 'Examples', target, 'Bluetooth', project);
    return new Promise((reject, resolve) => {
        const makeCmd = spawn('make', ['-j', fullPath]);
        makeCmd.stdout.on('data', data => { console.log(data) });
        makeCmd.stderr.on('data', data => { console.log(data) });
        makeCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
            reject(error);
        });
        makeCmd.on('close', code => {
            console.log(`Process exited with code ${code}`);
            elfPath = path.join(fullPath, 'build', `${target.toLowerCase()}.elf`);
            resolve(elfPath);
        });
    });
}

const main = async function () {
    let targetServer = await getTarget(BOARD_SERVER);
    let targetClient = await getTarget(BOARD_CLIENT);

    let elfServer = await makeProject(targetServer, SERVER);
    let elfClient = await makeProject(targetClient, CLIENT);

    options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: '../../tests',
        args: [targetServer, targetClient, elfServer, elfClient]
    };
    let otasTest = new PythonShell('otas_connected.py', options);
    otasTest.on('message', function (message) { console.log(message) });
    otasTest.end(function (err) {
        if (err) throw err;
        console.log('Test finished.')
    });
}

main();
