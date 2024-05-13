const Core = require('@actions/core');
const Github = require('@actions/github');
const { PythonShell } = require('python-shell');
const { env } = require('node:process');

const BOARD_IDS = Core.getMultilineInput('boards');
const LOCK_FLAG = Core.getBooleanInput('lock', {required: false});
const TIMEOUT = Core.getInput('timeout', {required: false });
const ALL_OWNED = Core.getBooleanInput('all_owned', {required: false});


const OWNER = Core.getInput('owner', {required: false }); 
const OWNER_REF = OWNER ? OWNER : Github.context.ref;

const main = async function() {
    var pyArgs = [];
    if(ALL_OWNED)
    {
        pyArgs = [
            '--unlock-owner', `${OWNER_REF}`,
        ]
    }
    else
    {
        let mode = LOCK_FLAG ? '-l' : '-u'
        pyArgs = [
            `${mode}`,
            // `${BOARD_IDS.join(" ")}`,
            ...BOARD_IDS,
            '--owner', `${OWNER_REF}`,
            '--timeout', `${TIMEOUT}`
        ]
    }
    
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: pyArgs
    };
    
    await PythonShell.run('resource_manager.py', options).then(
        (results) => console.log(results.join("\n")),
        (error) => console.error(error)
    );
   
}

main();
