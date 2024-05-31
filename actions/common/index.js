const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const  findTargetDirectory = function(dir, target) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        
        if (fs.lstatSync(fullPath).isDirectory()) {
            if (file === target) {
                return fullPath;
            }

            const found = findTargetDirectory(fullPath, target);
            if (found) {
                return found;
            }
        }
    }
    return null;
}

const getBoardData = function (boardId, itemName) {
    const args = ['-g', `${boardId}.${itemName}`]
    let boardData = [];
    return new Promise((resolve, reject) => {
        const getCmd = spawn('resource_manager', args);
        getCmd.stdout.on('data', (data) => { boardData.push(data.toString().trim()) });
        getCmd.stderr.on('data', (data) => { console.log(data.toString()) });
        getCmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        getCmd.on('close', (code) => {
            if (code !== 0) { 
                console.log(`Process exited with code ${code}`);
                reject(code);
            }
            console.log("%s --> %s", itemName, boardData[0]);
            resolve(boardData[0]);
        });
    });
}

const getBoardOwner = function (boardId) {
    const args = ['--get-owner', `${boardId}`]
    let ownerData = []
    return new Promise((resolve, reject) => {
        const getCmd = spawn('resource_manager', args);
        getCmd.stdout.on('data', (data) => { ownerData.push(data.toString().trim()) });
        getCmd.stderr.on('data', (data) => { console.log(data.toString()) });
        getCmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        getCmd.on('close', (code) => {
            if (code !== 0) {
                console.log(`Process exited with code ${code}`);
                reject(code);
            }
            console.log("owner --> %s", ownerData[0]);
            resolve(ownerData[0]);
        });
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

module.exports = { getBoardData, getBoardOwner, procSuccess, procFail, fileExists, findTargetDirectory };
