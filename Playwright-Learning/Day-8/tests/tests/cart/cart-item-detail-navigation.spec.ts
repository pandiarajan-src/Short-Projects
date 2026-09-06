// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';

test.describe('Shopping Cart Management', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Cart item click navigates to product detail page', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Add 'Sauce Labs Backpack' to the cart and open the cart page.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await expect(cartPage.rowByName('Sauce Labs Backpack')).toBeVisible();

    // 2. Click the product name link 'Sauce Labs Backpack' within the cart row.
    await cartPage.productLink('Sauce Labs Backpack').click();
    await expect(page).toHaveURL(/inventory-item\.html\?id=\d+/);
    await expect(page.getByText('Sauce Labs Backpack', { exact: true })).toBeVisible();
    await expect(page.getByText('carry.allTheThings() with the sleek', { exact: false })).toBeVisible();
    await expect(page.getByText('$29.99', { exact: true })).toBeVisible();
  });
});
