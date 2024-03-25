/**
 * Outputs all dynamically generated blockly block's code as follows:
 * - it uses `desktop.html` as the blockly page
 * - digs out the blocks from the toolbox object on the page with regex
 * - adds all the blocks one after the other
 * - for each block, it generates the code, saves it in the array
 *
 * This serves as a generic input for the HIL tests. If the generator
 * generates code which makes the robot throw errors, we will know about it.
 */

// For testing on localhost
// const BLOCKLY_URL = 'http://dev.localhost/robot/blockly/desktop.html'

// For testing from the latest deployed version of blockly, we use Supercharge's
// test environment and pull the blockly blocks from there.
const BLOCKLY_URL = 'https://test.rr.scapps.io/desktop.html'

const fs = require('fs');
const puppeteer = require('puppeteer');

async function runScripts() {
    const browser = await puppeteer.launch({
        dumpio: true
    });
    const page = await browser.newPage();
    await page.goto(BLOCKLY_URL);

    // Run your scripts here
    const generatedCode = await page.evaluate(async () => {
        const allToolboxXmls = Object.keys(toolboxes).map((tb) => toolboxes[tb].xml).join('\n')

        // Simple regex to get the block names in the toolbox.
        const regex = /type="(.*)"/g;
        const matches = [...allToolboxXmls.matchAll(regex)];

        // Now matches is an array of all match results
        // Each item is an array where the first element is the full match, and the rest are the capturing groups
        // So, to get the block names, you can map over the matches and get the second element of each item
        const blockNames = matches.map(match => match[1]);

        const getBlockCode = (id) => {
            const block = workspace.newBlock(id);
            block.initSvg();
            block.render();

            const pythonCode = Blockly.Python.workspaceToCode(workspace)
            block.dispose(true, true)
            return pythonCode
        }


        const blockCodeMap = {}

        blockNames.forEach((blockName) => blockCodeMap[blockName] = getBlockCode(blockName))

        return blockCodeMap
    });

    fs.writeFileSync('blocks.json', JSON.stringify(generatedCode, null, 2))

    console.log('Found blocks: ', Object.keys(generatedCode).length);

    console.log('Done')

    await browser.close();
}

runScripts().catch(console.error);