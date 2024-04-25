const Core = require('@actions/core');
const { spawn } = require('child_process');
const { procSuccess, procFail } = require('../common');

const BUILD_PATH = Core.getInput('path');
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });

const makeDistclean = function (projectPath) {
    return new Promise((resolve, reject) => {
        const cleanCmd = spawn('make', ['-C', projectPath, 'distclean']);
        cleanCmd.stdout.on('data', data => { console.log(data.toString().trim()) });
        cleanCmd.stderr.on('data', data => { console.log(data.toString().trim()) });
        cleanCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        cleanCmd.on('close', code => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const makeClean = function (projectPath) {
    return new Promise((resolve, reject) => {
        const cleanCmd = spawn('make', ['-C', projectPath, 'clean']);
        cleanCmd.stdout.on('data', data => { console.log(data.toString().trim()) });
        cleanCmd.stderr.on('data', data => { console.log(data.toString().trim()) });
        cleanCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        cleanCmd.on('close', code => {
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const makeProject = async function (projectPath, distclean) {
    console.log(projectPath)
    if (distclean) {
        await makeDistclean(projectPath);
    } else {
        await makeClean(projectPath);
    }

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
        });
    });
}

const main = async function () {
    await makeProject(BUILD_PATH, DISTCLEAN_FLAG).then(
        (success) => { return procSuccess(success, 'Build'); },
        (error) => { return procFail(error, 'Build', false); }
    );
}

main();

module.exports = { makeProject }