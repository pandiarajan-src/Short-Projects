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

    for (const {username, expectSuccess} of users) {
        test(`${username} login test`, async ({page}) => {
            const loginPage = new LoginPage(page);
            await loginPage.goToLoginPage();
            await loginPage.login(username, 'secret_sauce');
            if (expectSuccess) {
                await expect(page).toHaveURL(/inventory/);
            } else {
                await expect(page.getByText(/locked out/i)).toBeVisible();
            }
        });
    }

});
