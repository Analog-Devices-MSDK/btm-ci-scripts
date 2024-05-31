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
            cleanCmd.stderr.on('data', data => { dumpOut = `${dumpOut}${data.toString()}` });
        } else {
            cleanCmd.stdout.on('data', data => { logOut = `${logOut}${data.toString()}` });
            cleanCmd.stderr.on('data', data => { logOut = `${logOut}${data.toString()}` });
        }
        cleanCmd.on('error', error => {
            if (suppress) {
                logOut = `${logOut}${dumpOut}`
            }
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        cleanCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });

}

const makeProject = async function (projectPath, distclean, build_flags, board="", suppress=true) {
    let makeArgs = ['-j', '-C', projectPath];
    makeArgs.push(...build_flags);
    
    if(board != "")
    {
        makeArgs.push(`BOARD=${board}`)
    }
    
    let retVal = 0;
    await cleanProject(projectPath, distclean, suppress).then(
        (success) => procSuccess(success, 'Clean'),
        (error) => {
            retVal--;
            procFail(error, 'Clean', false);
        }
    );

    return new Promise((resolve, reject) => {
        let logOut = '';
        let dumpOut = '';
        if (retVal < 0) {
            console.log("i guess we exit here?")
            reject(retVal);
        }
        const makeCmd = spawn('make', makeArgs);
        console.log('here after creation')
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
            console.log('here')
            console.log(error.message)
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        makeCmd.on('close', code => {
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            console.log(code)
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
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
        (success) => procSuccess(success, "Build"),
        (error) => {
            retVal --;
            procFail(error, 'Build', false);
            Core.setFailed(`Build ${projPath} failed.`)
        }
    );
    if (retVal < 0) {
        return;
    }
}

if (require.main === module) {
    main();
}

module.exports = { makeProject };
