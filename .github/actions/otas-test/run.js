var execSync = require('child_process').execSync;
const core = require('@actions/core');
const github = require('@actions/github');

// const BOARD_SERVER = process.env.INPUT_BOARD_SERVER;
// const BOARD_CLIENT = process.env.INPUT_BOARD_CLIENT;
// const MSDK_PATH = process.env.INPUT_MSDK_PATH;

console.log("Current directory:", __dirname);

const BOARD_SERVER = core.getInput('board_server');
const BOARD_CLIENT = core.getInput('board_client');
const MSDK_PATH = core.getInput('msdk_path');

console.log(BOARD_SERVER);
console.log(BOARD_CLIENT);
console.log(MSDK_PATH);




let target_obj = "${BOARD_SERVER}.target"; 

let target_server =  execSync(['resource_manager.py', '-g' ,target_obj]);

const command = 'chmod +x run.sh && ./run.sh ' +  BOARD_SERVER + ' ' + BOARD_CLIENT + ' ' + MSDK_PATH;

exec(command,
    function (error, stdout, stderr) {
        console.log('stdout: ' + stdout);
        console.log('stderr: ' + stderr);
        if (error !== null) {
             console.log('exec error: ' + error);
        }
    });
