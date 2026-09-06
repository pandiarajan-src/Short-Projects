import {test, expect} from '@playwright/test';
import path from 'path';
import fs from 'fs';
import os from 'os';

test.describe('Iframes, popups, new tabs, uploads & downloads', () => {

    // --- iframe ---
    // frameLocator() scopes every subsequent locator to inside the frame, so
    // normal auto-waiting/retrying still applies — you never touch page.frame()
    // or manually poll for the frame to attach.
    //
    // We point at a pair of local fixture files (fixtures/iframe-parent.html
    // embedding fixtures/iframe-child.html) instead of a public iframe demo:
    // the well-known the-internet.herokuapp.com/iframe page embeds TinyMCE from
    // a third-party CDN that now rate-limits free loads, so that page can go
    // read-only mid-run through no fault of the test.
    test('fills and submits a form inside an iframe', async ({page}) => {
        const fixturePath = path.join(__dirname, 'fixtures', 'iframe-parent.html');
        await page.goto(`file://${fixturePath}`);

        const frame = page.frameLocator('#my-iframe');
        await frame.getByLabel('Name').fill('Pandi');
        await frame.getByRole('button', {name: 'Submit'}).click();

        await expect(frame.locator('#result')).toHaveText('Submitted!');
    });

    // --- popup / new tab ---
    // Clicking a target="_blank" link doesn't navigate the current page — it
    // opens a second Page on the same BrowserContext. You have to start
    // listening for the "page" event before the click, otherwise the new tab
    // can open and you'd miss it (classic race condition).
    test('opens a new tab and switches to it', async ({page, context}) => {
        await page.goto('https://the-internet.herokuapp.com/windows');

        const [newPage] = await Promise.all([
            context.waitForEvent('page'),
            page.getByRole('link', {name: 'Click Here'}).click(),
        ]);
        await newPage.waitForLoadState();

        await expect(newPage).toHaveTitle('New Window');
    });

    // --- file upload ---
    test('uploads a file and the server confirms it', async ({page}) => {
        await page.goto('https://the-internet.herokuapp.com/upload');

        // this input has no associated <label>, so getByLabel isn't an option
        // here — id-based locator it is
        await page.locator('#file-upload').setInputFiles(path.join(__dirname, 'fixtures', 'sample-upload.txt'));
        await page.locator('#file-submit').click();

        await expect(page.getByRole('heading', {name: 'File Uploaded!'})).toBeVisible();
        await expect(page.getByText('sample-upload.txt')).toBeVisible();
    });

    // --- file download ---
    // the-internet's /download page lists files from one folder shared by
    // every visitor running this exact demo, so an existing filename could
    // vanish between when we read this test and when it runs. We make the
    // test self-contained instead: upload a file with a name unique to this
    // run, then immediately download that same file back.
    test('uploads then downloads the same file to prove the round trip', async ({page}) => {
        const fileName = `playwright-demo-${Date.now()}.txt`;
        const uploadPath = path.join(os.tmpdir(), fileName);
        fs.writeFileSync(uploadPath, 'round-trip download demo file');

        await page.goto('https://the-internet.herokuapp.com/upload');
        await page.locator('#file-upload').setInputFiles(uploadPath);
        await page.locator('#file-submit').click();
        await expect(page.getByRole('heading', {name: 'File Uploaded!'})).toBeVisible();

        await page.goto('https://the-internet.herokuapp.com/download');
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            page.getByRole('link', {name: fileName}).click(),
        ]);

        const savedPath = path.join(os.tmpdir(), `downloaded-${fileName}`);
        console.log('Saving downloaded file to', savedPath);
        await download.saveAs(savedPath);
        expect(fs.existsSync(savedPath)).toBeTruthy();
    });

});
