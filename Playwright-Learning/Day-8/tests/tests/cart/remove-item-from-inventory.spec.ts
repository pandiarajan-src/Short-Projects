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

  test('Remove an item from the inventory page after adding it', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Add 'Sauce Labs Backpack' and 'Sauce Labs Bike Light' to the cart from the inventory page.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.addProductToCart('sauce-labs-bike-light');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('2');

    // 2. Click [data-test="remove-sauce-labs-backpack"] (the same button, now showing 'Remove') on the inventory page.
    await inventoryPage.removeProductFromCart('sauce-labs-backpack');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');
    await expect(inventoryPage.addToCartButton('sauce-labs-backpack')).toHaveText('Add to cart');

    // 3. Open the cart page.
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(1);
    await expect(cartPage.rowByName('Sauce Labs Bike Light')).toBeVisible();
    await expect(cartPage.rowByName('Sauce Labs Backpack')).toHaveCount(0);
  });
});
