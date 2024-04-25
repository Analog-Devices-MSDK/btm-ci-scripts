const { PythonShell } = require('python-shell');
const { env } = require('node:process');

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
    console.log('%s successful.', procName);
    return exitCode;
}

const procFail = function(exitCode, procName, retry) {
    if (retry) {
        console.log('!! ERROR: %s failed. Retrying 1 time. !!', procName);
    } else {
        console.log('!! ERROR: %s failed. Aborting. !!', procName);
    }
    return exitCode;
}

module.exports = { getBoardData, getBoardOwner, procSuccess, procFail };
