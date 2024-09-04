const Core = require('@actions/core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('node:fs')
const { procSuccess, procFail, findTargetDirectory } = require('../common');

const cleanProject = function (projectPath, distclean, suppress) {
    let cleanOpt = distclean ? 'distclean' : 'clean';
    
    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
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

const makeProject = async function (projectPath, distclean, build_flags, board="", suppress=true, logfile=null) {
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

    let logOut = '';
    let dumpOut = '';
    return new Promise((resolve, reject) => {
        if (retVal < 0) {
            reject(retVal);
        }
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
            logOut = `${logOut}ERROR: ${error.message}`;
        });
        makeCmd.on('close', code => {
            if (logfile !== null) {
                if (suppress && code === 0) {
                    logOut = `${logOut}${dumpOut}`
                }
                try {
                    fs.writeFileSync(logfile, logOut);
                } catch (err) {
                    console.error(err);
                }
            }
            logOut = `${logOut}Process exited with code ${code}`;
            console.log(logOut);
            if (code != 0) reject(code);
            else {
                resolve(code);
            }
        });
    });
}

const main = async function () {
    const PROJECT_DIRS = Core.getMultilineInput('project');
    const TARGETS = Core.getMultilineInput('targets', { required: false });
    const MSDK_PATH = Core.getInput('msdk_path', { required: false });
    const DISTCLEAN_FLAG = Core.getBooleanInput('distclean', { required: false });
    const BUILD_FLAGS = Core.getMultilineInput('build_flags', { required: false });
    const SUPPRESS_FLAG = Core.getBooleanInput('suppress_output', { required: false });
    const USE_LOGFILE = Core.getBooleanInput('create_buildlog', { required: false });
    let build_flags = [];
    let retVal = 0;
    let logDir = "";
    if (USE_LOGFILE) {
        logDir = "build-logs";
        fs.mkdir(logDir, (err) => {
            if (err) {
                console.error(err)
                throw err
            }
        });
    }
    for (var i=0; i<BUILD_FLAGS.length; i++) {
        build_flags.push(...BUILD_FLAGS[i].split(" "))
    }
    if (TARGETS.length === 0) {
        for (let i = 0; i < PROJECT_DIRS.length; i++) {
            let logPath = null;
            if (USE_LOGFILE) {
                logPath = path.join(logDir, `build-log-${i}.txt`)
            }
            let buildPath = PROJECT_DIRS[i];
            await makeProject(buildPath, DISTCLEAN_FLAG, build_flags, board="", suppress=SUPPRESS_FLAG, logfile=logPath).then(
                (success) => procSuccess(success, "Build"),
                (error) => {
                    retVal --;
                    procFail(error, 'Build', false);
                    Core.setFailed(`Build ${buildPath} failed.`)
                }
            );
        }
    } else {
        if (PROJECT_DIRS.length === 1 && TARGETS.length > 1) {
            for (let i = 0; i < TARGETS.length; i++) {
                PROJECT_DIRS[i] == PROJECT_DIRS[0];
            }
        } else if (PROJECT_DIRS.length > 1 && TARGETS.length === 1) {
            for (let i = 0; i < PROJECT_DIRS.length; i++) {
                TARGETS[i] = TARGETS[0]
            }
        } else if (PROJECT_DIRS.length !== TARGETS.length) {
            console.log("Length of project list must be 1 or the same as length of targets list.");
            throw new Error(
                "!! ERROR: Mismatched parameter lengths. Unclear which projects to build. !!"
            );
        }
        for (let i = 0; i < TARGETS.length; i++) {
            let logPath = null;
            if (USE_LOGFILE) {
                logPath = path.join(logDir, `build-log-${i}.txt`)
            }
            let buildPath = findTargetDirectory(path.join(MSDK_PATH, "Examples", TARGETS[i]), PROJECT_DIRS[i])
            await makeProject(buildPath, DISTCLEAN_FLAG, build_flags, board="", suppress=SUPPRESS_FLAG, logfile=logPath).then(
                (success) => procSuccess(success, "Build"),
                (error) => {
                    retVal--;
                    procFail(error, "Build", false);
                    Core.setFailed(`Build ${buildPath} failed.`)
                }
            );
        }
    }
    
    Core.setOutput("log_directory", logDir)

    if (retVal < 0) {
        return;
    }
}

if (require.main === module) {
    main();
}

module.exports = { makeProject };
