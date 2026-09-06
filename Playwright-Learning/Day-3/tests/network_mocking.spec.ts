import {test, expect} from '@playwright/test';
import {LoginPage} from '../pages/LoginPage';
import {InventoryPage} from '../pages/InventoryPage';
import {LogoutPage} from '../pages/LogoutPage';
import {user_names, users} from './common_ds';

test.describe('SauceDemo Login Tests', () => {

    // runs once, before any test in this describe block
    test.beforeAll(async () => {
        console.log('Starting SauceDemo suite');
    });

    // runs before EVERY test below — good for "always start logged out"
    test.beforeEach(async ({ page }) => {
        console.log('New test starting:', test.info().title);
    });

    test('adding couple of items updates the cart badge', async ({page}) => {

        const loginPage = new LoginPage(page);
        await loginPage.goToLoginPage();
        await loginPage.login('standard_user', 'secret_sauce');
        await expect(page).toHaveURL(/inventory/);

        await page.goto('https://www.saucedemo.com/inventory.html');
        const inventoryPage = new InventoryPage(page);
        const itemsToAdd = ['Sauce Labs Backpack', 'Sauce Labs Bike Light'];

        for (const item of itemsToAdd) {
            await inventoryPage.addItemToCart(item);
        }

        // use locator scoping with .filter() instead of relying on indexes
        await expect(page.locator('.shopping_cart_badge').filter({ hasText: String(itemsToAdd.length) })).toBeVisible();
    });

    // --- Network interception / mocking ---
    // One of Playwright's biggest advantages over Selenium: you can intercept
    // and mock network calls with page.route(), no external proxy tool needed.
    //
    // Note: SauceDemo doesn't fetch product data from a JSON API — the product
    // list is bundled straight into its JS, so there's no "**/api/products"
    // call to mock here. What it DOES fetch over the network are the product
    // images, so we mock one of those to show the technique working for real.

    test('mocks the backpack product image with a fake response', async ({page}) => {
        const loginPage = new LoginPage(page);
        await loginPage.goToLoginPage();
        await loginPage.login('standard_user', 'secret_sauce');
        await expect(page).toHaveURL(/inventory/);

        // a tiny SVG used as fake "mocked" image content — the browser renders
        // it fine in an <img> even though the URL ends in .jpg, because the
        // Content-Type header (not the extension) decides how it's parsed
        const mockedImage = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="hotpink"/></svg>';

        await page.route('**/sauce-backpack*.jpg', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'image/svg+xml',
                body: mockedImage,
            });
        });

        // reload so the route we just registered intercepts the image fetch
        await page.reload();

        // the mocked response still renders as a valid image, no broken-image icon
        await expect(page.getByRole('img', {name: 'Sauce Labs Backpack'})).toBeVisible();
    });

    test('simulates a broken image request to test how the page copes with errors', async ({page}) => {
        const loginPage = new LoginPage(page);
        await loginPage.goToLoginPage();
        await loginPage.login('standard_user', 'secret_sauce');
        await expect(page).toHaveURL(/inventory/);

        // force the backpack image request to fail server-side — testing an
        // error edge case without needing the real backend to misbehave
        await page.route('**/sauce-backpack*.jpg', async (route) => {
            await route.fulfill({status: 500, body: 'Internal Server Error'});
        });

        await page.reload();

        // even though its image request failed, the rest of the page — and the
        // product name/price/add-to-cart flow — should still work fine
        await expect(page.locator('.inventory_item').filter({hasText: 'Sauce Labs Backpack'})).toBeVisible();
    });

});
