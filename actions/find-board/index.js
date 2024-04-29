const Core = require('@actions/core');
const { PythonShell } = require('python-shell');

const TARGET_NAMES = Core.getMultilineInput('target');
const GROUPS = Core.getMultilineInput('group');
const NUM_BOARDS = parseInt(Core.getInput('num_boards'), 10);

const findBoardList = function (target, group) {
    let options = {
        mode: 'text',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: env.RESOURCE_SHARE_DIR,
        args: ['--find-board', `${target} ${group}`]
    };
    return new Promise((resolve, reject) => {
        PythonShell.run('resource_manager.py', options).then(
            (item) => { console.log('Found: %s', item[0]); resolve(item[0]); },
            (error) => reject(error)
        );
    });
}

const main = async function() {
    if (GROUPS.length === 1 && TARGET_NAMES.length > 1) {
        for (let i = 0; i < TARGET_NAMES.length; i++) {
            GROUPS[i] = GROUPS[0];
        }
    } else if (TARGET_NAMES.length === 1 && GROUPS.length > 1) {
        for (let i = 0; i < GROUPS.length; i++) {
            TARGET_NAMES[i] = TARGET_NAMES[0];
        }
    } else if (GROUPS.length !== TARGET_NAMES.length) {
        console.log(
            "Target and groups lists can only have different lengths when one length is 1."
        );
        throw new Error(
            '!! ERROR: Mismatched parameter lengths. Boards could not be selected. !!'
        );
    }
    var retBoards = '';
    if (GROUPS.length === 1 && TARGET_NAMES.length === 1) {
        let matches = findBoardList(TARGET_NAMES[0], GROUPS[0]).split(" ");
        if (matches.length < NUM_BOARDS) {
            throw new Error('!! ERROR: Not enough matches to fill desired amount of boards. !!');
        }
        for (let i = 0; i < NUM_BOARDS; i++) {
            retBoards = `${retBoards} ${matches[i]}`;
        }
    } else {
        let matches = [];
        let valid = [];
        for (let i = 0; i < GROUPS.length; i++) {
            matches[i] = findBoardList(TARGET_NAMES[i], GROUPS[i].split(" "));
            valid[i] = Array(matches[i].length).fill(true);
        }
        for (let i = 0; i < GROUPS.length; i++) {
            let match = matches[i][valid[i].indexOf(true)];
            for (let j = i+1; j < GROUPS.length; j++) {
                if (matches[j].indexOf(match) !== -1) {
                    valid[j][matches[j].indexOf(match)] = false;
                }
            }
            retBoards = `${retBoards} ${match}`;
        }
    }
    Core.setOutput('board_ids', retBoards.trim());
}
main()