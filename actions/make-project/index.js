const Core = require('@actions/core');
const { spawn } = require('child_process');
const { procSuccess, procFail } = require('../common');

const BUILD_PATH = Core.getInput('path');
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });
const SUPPRESS_FLAG = Core.getBooleanInput('suppress_output', { required: false });

const cleanProject = function (projectPath, distclean, suppress) {
    let cleanOpt = distclean ? 'distclean' : 'clean';
    return new Promise((resolve, reject) => {
        let logOut = '';
        let dumpOut = '';
        const cleanCmd = spawn('make', ['-C', projectPath, cleanOpt]);
        if (suppress) {
            cleanCmd.stdout.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            cleanCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        }
        cleanCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        cleanCmd.on('error', error => {
            console.error(`ERROR: ${error.message}`);
        });
        cleanCmd.on('close', code => {
            console.log(logOut);
            console.log(`Process exited with code ${code}`);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const makeProject = async function (projectPath, distclean, suppress) {
    await cleanProject(projectPath, distclean, suppress).then(
        (success) => procSuccess(success, 'Clean'),
        (error) => procFail(error, 'Clean', false)
    );
    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        const makeCmd = spawn('make', ['-j', '-C', projectPath]);
        if (suppress) {
            makeCmd.stdout.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            makeCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
        }
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
    await makeProject(BUILD_PATH, DISTCLEAN_FLAG, SUPPRESS_FLAG).then(
        (success) => procSuccess(success, 'Build'),
        (error) => procFail(error, 'Build', false)
    );
}

if (require.main === module) {
    main();
}

module.exports = { makeProject };