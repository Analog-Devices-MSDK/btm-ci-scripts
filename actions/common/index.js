const { PythonShell } = require('python-shell');
const { env } = require('node:process');
const fs = require('fs')

const getBoardData = function (boardId, itemName) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['-g', `${boardId}.${itemName}`]
    };
    return new Promise((resolve, reject) => {
        PythonShell.run('resource_manager.py', options).then(
            (item) => { console.log('%s --> %s', itemName, item[0]); resolve(item[0]); },
            (error) => reject(error)
        );
    });
}

const getBoardOwner = function (boardId) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['--get-owner', `${boardId}`]
    };
    return new Promise((resolve, reject) => {
        PythonShell.run('resource_manager.py', options).then(
            (ownerId) => {console.log('owner --> %s', ownerId[0]); resolve(ownerId[0]) },
            (error) => reject(error)
        );
    });
}

const procSuccess = function(exitCode, procName) {
    console.log('%s successful. (%s)', procName, `${exitCode}`);
}

const procFail = function(exitCode, procName, retry) {
    if (retry) {
        console.log('!! ERROR(%s): %s failed. Retrying 1 time. !!', `${exitCode}`, procName);
    } else {
        console.log('!! ERROR(%s): %s failed. Aborting. !!', `${exitCode}`, procName);
    }
}

const fileExists = async path => !!(await fs.promises.stat(path).catch(e => false));

module.exports = { getBoardData, getBoardOwner, procSuccess, procFail, fileExists };
