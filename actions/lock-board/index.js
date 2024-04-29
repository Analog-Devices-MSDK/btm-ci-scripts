const Core = require('@actions/core');
const Github = require('@actions/github');
<<<<<<< HEAD:actions/lock-board/run.js
const {
    PythonShell
} = require('python-shell');

const BOARD_IDS = Core.getMultilineInput('boards');
const LOCK_FLAG = Core.getBooleanInput('lock', {
    required: false
});
=======
const { PythonShell } = require('python-shell');
const { env } = require('node:process');

const BOARD_IDS = Core.getMultilineInput('boards');
const LOCK_FLAG = Core.getBooleanInput('lock', {required: false});
const TIMEOUT = Core.getInput('timeout', {required: false });
>>>>>>> main:actions/lock-board/index.js
const OWNER_REF = Github.context.ref;

const main = async function() {
    let mode = LOCK_FLAG ? '-l' : '-u'
    let pyArgs = [
        `${mode}`,
        `${BOARD_IDS.join(" ")}`,
        '--owner', `${OWNER_REF}`,
        '--timeout', `${TIMEOUT}`
    ]
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: pyArgs
    };
<<<<<<< HEAD:actions/lock-board/run.js
    PythonShell.run('resource_manager.py', options, function(err, results) {
        if (err) throw err;
        console.log(results)
    })
=======
    await PythonShell.run('resource_manager.py', options).then(
        (results) => console.log(results.join("\n")),
        (error) => console.error(error)
    );
>>>>>>> main:actions/lock-board/index.js
}

main();