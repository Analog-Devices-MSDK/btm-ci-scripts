const fs = require('fs')
const execSync = require('child_process').execSync;
const core = require('@actions/core');
const github = require('@actions/github');
const { exit } = require('process');

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




let target_client = execSync("resource_manager.py -g ${BOARD_CLIENT}.target");
console.log(target_client);
let target_server = execSync("resource_manager.py -g ${BOARD_SERVER}.target");

let target_client_obj_lower = target_client_obj.toLowerCase();
let target_server_obj_lower = target_server_obj.toLowerCase();




console.log(target_client_obj);
console.log(target_server_obj);


const OTAS_PATH = "${MSDK_PATH}/Examples/${target_server}/Bluetooth/BLE_otas"
const OTAC_PATH = "${MSDK_PATH}/Examples/${target_client}/Bluetooth/BLE_otac"

execSync("make -j -C ${OTAS_PATH}");
execSync("make -j -C ${OTAC_PATH}");


const elf_server = "${OTAS_PATH}/build/${target_lower}.elf"
const elf_client = "${OTAC_PATH}/build/${target_lower}.elf"


if(!fs.existsSync(elf_server))
{
    console.log("${elf_server} DNE!")
    exit(-1);
}
else if(!fs.existsSync(elf_client))
{
    console.log("${elf_client} DNE!")
    exit(-1);
}

command = "cd ../../../tests && python3 otas_connected.py ${target_server} ${target_client} ${elf_server} ${elf_client}"

let ret = execSync(command);

if(ret )



exec(command,
    function (error, stdout, stderr) {
        console.log('stdout: ' + stdout);
        console.log('stderr: ' + stderr);
        if (error !== null) {
            console.log('exec error: ' + error);
        }
    });
