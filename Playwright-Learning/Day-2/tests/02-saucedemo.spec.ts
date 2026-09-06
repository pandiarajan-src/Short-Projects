import {test, expect} from '@playwright/test';
import {LoginPage} from '../pages/LoginPage';
import {InventoryPage} from '../pages/InventoryPage';
import {LogoutPage} from '../pages/LogoutPage';

test.describe('SauceDemo Login Tests', () => {

    // runs once, before any test in this describe block
    test.beforeAll(async () => {
        console.log('Starting SauceDemo suite');
    });

    // runs before EVERY test below — good for "always start logged out"
    test.beforeEach(async ({ page }) => {
        console.log('New test starting:', test.info().title);
    });

    test('Standard User can Login', async ({page}) => {
        const loginPage = new LoginPage(page);
        await loginPage.goToLoginPage();
        await loginPage.login('standard_user', 'secret_sauce');
        await expect(page).toHaveURL(/inventory/);
    });

    test('Locked Out User cannot Login', async ({page}) => {
        const loginPage = new LoginPage(page);
        await loginPage.goToLoginPage();
        await loginPage.login('locked_out_user', 'secret_sauce');
        await expect(page.getByText(/locked out/i)).toBeVisible();
    });

    test('adding an item updates the cart badge', async ({page}) => {

        await page.goto('https://www.saucedemo.com/inventory.html');
        const inventoryPage = new InventoryPage(page);
        await inventoryPage.addItemToCart('Sauce Labs Backpack');
        // scope the badge locator and assert by its text using .filter()
        await expect(page.locator('.shopping_cart_badge').filter({ hasText: '1' })).toBeVisible();
    });

    test('adding couple of items updates the cart badge', async ({page}) => {

        await page.goto('https://www.saucedemo.com/inventory.html');
        const inventoryPage = new InventoryPage(page);
        const itemsToAdd = ['Sauce Labs Backpack', 'Sauce Labs Bike Light'];

        for (const item of itemsToAdd) {
            await inventoryPage.addItemToCart(item);
        }

        // use locator scoping with .filter() instead of relying on indexes
        await expect(page.locator('.shopping_cart_badge').filter({ hasText: String(itemsToAdd.length) })).toBeVisible();
    });

    test('user can logout', async ({page}) => {
        await page.goto('https://www.saucedemo.com/inventory.html');
        const logoutPage = new LogoutPage(page);
        await logoutPage.logout();
        await expect(page).toHaveURL('https://www.saucedemo.com/');
    });

    // runs after EVERY test — cleanup, screenshots on failure, etc.
    test.afterEach(async ({ page }, testInfo) => {
        if (testInfo.status !== testInfo.expectedStatus) {
        await page.screenshot({ path: `failure-${testInfo.title}.png` });
        }
    });

    // runs once, after all tests in this block finish
    test.afterAll(async () => {
        console.log('SauceDemo suite done');
    });

});