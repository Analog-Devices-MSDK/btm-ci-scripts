var exec = require('child_process').exec;

const BOARD_SERVER = process.env.INPUT_BOARD_SERVER;
const BOARD_CLIENT = process.env.INPUT_BOARD_CLIENT;
const MSDK_PATH = process.env.INPUT_MSDK_PATH;

const command = 'chmod +x run.sh && ./run.sh ' +  BOARD_SERVER + ' ' + BOARD_CLIENT + ' ' + MSDK_PATH;

exec(command,
    function (error, stdout, stderr) {
        console.log('stdout: ' + stdout);
        console.log('stderr: ' + stderr);
        if (error !== null) {
             console.log('exec error: ' + error);
        }
    });
