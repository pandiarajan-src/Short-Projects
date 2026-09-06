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

  test('Remove an item from the cart page', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Add 'Sauce Labs Backpack', 'Sauce Labs Bike Light', and 'Sauce Labs Onesie' to the cart,
    // then navigate to the cart page.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.addProductToCart('sauce-labs-bike-light');
    await inventoryPage.addProductToCart('sauce-labs-onesie');
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(3);
    await expect(cartPage.shoppingCartBadge).toHaveText('3');

    // 2. Click the 'Remove' button on the 'Sauce Labs Bike Light' row.
    await cartPage.removeItem('sauce-labs-bike-light');
    await expect(cartPage.rowByName('Sauce Labs Bike Light')).toHaveCount(0);
    await expect(cartPage.shoppingCartBadge).toHaveText('2');
    await expect(cartPage.rowByName('Sauce Labs Backpack')).toBeVisible();
    await expect(cartPage.quantityByName('Sauce Labs Backpack')).toHaveText('1');
    await expect(cartPage.priceByName('Sauce Labs Backpack')).toHaveText('$29.99');
    await expect(cartPage.rowByName('Sauce Labs Onesie')).toBeVisible();
    await expect(cartPage.quantityByName('Sauce Labs Onesie')).toHaveText('1');
    await expect(cartPage.priceByName('Sauce Labs Onesie')).toHaveText('$7.99');
  });
});
