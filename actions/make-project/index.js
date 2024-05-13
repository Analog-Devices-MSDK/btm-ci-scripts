const Core = require('@actions/core');
const { spawn } = require('child_process');
const { procSuccess, procFail } = require('../common');

const BUILD_PATH = Core.getInput('path');
const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });
const BUILD_FLAGS = Core.getMultilineInput('build_flags', { required: false });
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
            // console.error(`ERROR: ${error.message}`);
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        cleanCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            // console.log(`Process exited with code ${code}`);
            // if (code != 0) reject(code);
            // else {
            //     resolve(code);
            // }
            resolve(code);
        });
    });

}

const makeProject = async function (projectPath, distclean, build_flags, suppress) {
    let makeArgs = ['-j', '-C', projectPath];
    makeArgs.push(...build_flags);

    retVal = await cleanProject(projectPath, distclean, suppress).then(
        (success) => procSuccess(success, 'Clean'),
        (error) => procFail(error, 'Clean', false)
    );

    if (retVal !== 0) {
        return new Promise((resolve, reject) => resolve(1));
    }

    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        const makeCmd = spawn('make', makeArgs);
        if (suppress) {
            makeCmd.stdout.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
            makeCmd.stderr.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            makeCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
            makeCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        }
        makeCmd.on('error', error => {
            if (suppress) {
                logOut = `${logOut}${dumpOut}`
            }
            // console.error(`ERROR: ${error.message}`);
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        makeCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            // console.log(`Process exited with code ${code}`);
            // if (code != 0) reject(code);
            // else {
            //     resolve(code);
            // }
            resolve(code);
        });
    });
}

const main = async function () {
    let build_flags = [];
    let retVal = 0;
    for (var i=0; i<BUILD_FLAGS.length; i++) {
        build_flags.push(...BUILD_FLAGS[i].split(" "))
    }
    await makeProject(BUILD_PATH, DISTCLEAN_FLAG, SUPPRESS_FLAG).then(
        (value) => {
            if (value === 0) {
                procSuccess(success, 'Build');
            } else {
                retVal --;
                procFail(value, 'Build', false);
                Core.setFailed(`Build ${projPath} failed.`)
            }
        },
        (error) => {
            retVal --;
            procFail(error, 'Build', false);
            Core.setFailed(`Build ${projPath} failed.`)
        }
    );
}

if (require.main === module) {
    main();
}

module.exports = { makeProject };
