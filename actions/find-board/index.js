const Core = require('@actions/core');
const { spawn } = require('child_process')

const TARGET_NAMES = Core.getMultilineInput('target');
const GROUPS = Core.getMultilineInput('group');
const NUM_BOARDS = parseInt(Core.getInput('num_boards'), 10);

const findBoardList = function (target, group) {
    const args = ["--find-board", `${target}`, `${group}`];
    let foundBoards = [];
    return new Promise((resolve, reject) => {
        const findCmd = spawn('resource_manager', args);
        findCmd.stdout.on('data', (data) => { foundBoards.push(data.toString()) });
        findCmd.stderr.on('data', (data) => { console.log(data.toString()) });
        findCmd.on('error', (error) => { console.log(`ERROR: ${error.message}`) });
        findCmd.on('close', (code) => {
            if (code !== 0) {
                console.log(`Process exited with code ${code}`);
                reject(code);
            }
            console.log("Found: %s", foundBoards[0]);
            resolve(foundBoards[0]);
        })
    })
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
    let retBoards = [];
    if (GROUPS.length === 1 && TARGET_NAMES.length === 1) {
        let matches = await findBoardList(TARGET_NAMES[0], GROUPS[0]).split(" ");
        if (matches.length < NUM_BOARDS) {
            throw new Error('!! ERROR: Not enough matches to fill desired amount of boards. !!');
        }
        for (let i = 0; i < NUM_BOARDS; i++) {
            retBoards.push(matches[i]);
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
            retBoards.push(match);
        }
    }

    for (let i = 0; i < 10; i++) {
        if (i >= retBoards.length) {
            Core.setOutput(`board${i+1}`, "");
        } else {
            Core.setOutput(`board${i+1}`, retBoards[i]);
        }
    }
}
main()
