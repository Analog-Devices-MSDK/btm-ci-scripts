const Core = require('@actions/core');
const Github = require('@actions/github');
const { env } = require('node:process');
const { ALL } = require('node:dns');

const BOARD_IDS = Core.getMultilineInput('boards');
const LOCK_FLAG = Core.getBooleanInput('lock', {required: false});
const TIMEOUT = Core.getInput('timeout', {required: false });
const ALL_OWNED = Core.getBooleanInput('all_owned', {required: false});


const OWNER = Core.getInput('owner', {required: false }); 
const OWNER_REF = OWNER ? OWNER : Github.context.ref;

const lock = function (boardIds, ownerRef, timeout) {
    const args = ['-l', ...boardIds, '--owner', `${ownerRef}`, '--timeout', `${timeout}`];
    console.log("HERE================================================================================");
    return new Promise((resolve, reject) => {
        const cmd = spawn('resource_manager', args);
        cmd.stdout.on('data', (data) => { console.log(data.toString()) });
        cmd.stderr.on('data', (data) => { console.log(data.toString()) });
        cmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        cmd.on('close', (code) => {
            if (code !== 0) {
                console.log('Lock failed.');
                reject(code);
            }
            resolve(code);
        })
    })
}

const unlock = function (boardIds, ownerRef, timeout) {
    const args = ['-u', ...boardIds, '--owner', `${ownerRef}`, '--timeout', `${timeout}`];
    return new Promise((resolve, reject) => {
        const cmd = spawn('resource_manager', args);
        cmd.stdout.on('data', (data) => { console.log(data.toString()) });
        cmd.stderr.on('data', (data) => { console.log(data.toString()) });
        cmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        cmd.on('close', (code) => {
            if (code !== 0) {
                console.log('Unlock failed.');
                reject(code);
            }
            resolve(code);
        })
    })

}

const unlockOwner = function (ownerRef) {
    const args = ['unlock-owner', `${ownerRef}`];
    return new Promise((resolve, reject) => {
        const cmd = spawn('resource_manager', args);
        cmd.stdout.on('data', (data) => { console.log(data.toString()) });
        cmd.stderr.on('data', (data) => { console.log(data.toString()) });
        cmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        cmd.on('close', (code) => {
            if (code !== 0) {
                console.log(`Unlock all failed.`);
                reject(code);
            }
            resolve(code);
        })
    })
}

const main = async function () {
    if (ALL_OWNED) {
        await unlockOwner(OWNER_REF).catch((err) => { Core.setFailed("Unlock all failed.") });
    } else if (LOCK_FLAG) {
        await lock(BOARD_IDS, OWNER_REF, TIMEOUT).catch((err) => { Core.setFailed("Lock failed") });
    } else {
        await unlock(BOARD_IDS, OWNER_REF, TIMEOUT).catch((err) => { Core.setFailed("Unlock failed.")});
    }
   
}

main();
