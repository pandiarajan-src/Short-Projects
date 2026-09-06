import { test as setup, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

setup('login in before each test', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goToLoginPage();
    await loginPage.login('standard_user', 'secret_sauce');
    await expect(page).toHaveURL(/inventory/);
    await page.context().storageState({ path: 'storageState.json' });
});
