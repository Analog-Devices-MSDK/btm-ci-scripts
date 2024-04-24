const Core = require('@actions/core');
const Github = require('@actions/github');
const { PythonShell } = require('python-shell');
const { env } = require('node:process');

const BOARD_IDS = Core.getMultilineInput('boards');
const LOCK_FLAG = Core.getBooleanInput('lock', {required: false});
const OWNER_REF = Github.context.ref;

const main = async function () {
    let mode = LOCK_FLAG ? '-l' : '-u'
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: [`${mode} ${BOARD_IDS.join(" ")} --owner ${OWNER_REF}`]
    };
    PythonShell.run('resource_manager.py', options, function (err, results) {
        if (err) throw err;
        console.log(results)
    })
}

main();
