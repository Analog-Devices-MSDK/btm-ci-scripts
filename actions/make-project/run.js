const Core = require('@actions/core');
const { spawn } = require('child_process');
const { procSuccess, procFail } = require('../common');

const BUILD_PATH = Core.getInput('path');
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });

const cleanProject = function (projectPath, distclean) {
    let cleanOpt = distclean ? 'distclean' : 'clean';
    let logOut = '';
    return new Promise((resolve, reject) => {
        const cleanCmd = spawn('make', ['-C', projectPath, cleanOpt]);
        cleanCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        cleanCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        cleanCmd.on('error', error => {
            console.log(logOut);
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
    await cleanProject(projectPath, distclean).then(
        (success) => procSuccess(success, 'Clean'),
        (error) => procFail(error, 'Clean', false)
    );
    let logOut = '';
    return new Promise((resolve, reject) => {
        const makeCmd = spawn('make', ['-j', '-C', projectPath]);
        makeCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        makeCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        makeCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        makeCmd.on('close', code => {
            console.log(logOut);
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
        (success) => procSuccess(success, 'Build'),
        (error) => procFail(error, 'Build', false)
    );
}

if (require.main === module) {
    main();
}

module.exports = { makeProject };