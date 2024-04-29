const Core = require('@actions/core');
const { PythonShell } = require('python-shell');
const path = require('path');
const { env } = require('node:process');
const { getBoardData, procSuccess, procFail } = require('../common');
const { makeProject } = require('../make-project');

const BOARD_CLIENT = Core.getInput('board_client');
const BOARD_SERVER = Core.getInput('board_server');
const MSDK_PATH = Core.getInput('msdk_path');

const runOtasTest = function (targetServer, targetClient, elfServer, elfClient) {
    options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.TESTS_DIR,
        args: [targetServer, targetClient, elfServer, elfClient]
    }
    return new Promise((resolve, reject) => {
        let pyshell = new PythonShell('otas_connected.py', options);
        pyshell.on('message', (message) => console.log(message));
        pyshell.end((err, code, signal) => {
            console.log('Process exited with code ' + code);
            console.log('The exit signal was: ' + signal);
            if (err) {
                console.log(err)
                reject(code);
            } else {
                resolve(code);
            }
        });
    });
}

const main = async function() {
    let [targetServer, targetClient] = await Promise.all([
        getBoardData(BOARD_SERVER, 'target'),
        getBoardData(BOARD_CLIENT, 'target')
    ]);
    let projectServer = path.join(MSDK_PATH, 'Examples', targetServer, 'Bluetooth', 'BLE_otas');
    console.log(projectServer);
    let projectClient = path.join(MSDK_PATH, 'Examples', targetClient, 'Bluetooth', 'BLE_otac');
    await Promise.all([
        makeProject(projectServer, false),
        makeProject(projectClient, false)
    ]);
    let elfServer = path.join(projectServer, 'build', `${targetServer.toLowerCase()}.elf`);
    let elfClient = path.join(projectClient, 'build', `${targetClient.toLowerCase()}.elf`);
    retCode = await runOtasTest(targetServer, targetClient, elfServer, elfClient).then(
        (success) => procSuccess(success, 'OTAS Test'),
        (error) => procFail(error, 'OTAS Test', false)
    );
    if (retCode === 0) {
        console.log('Test successful!');
    } else {
        console.log('Test failed.');
    }
}

main();
