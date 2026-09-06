// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';

test.describe('Product Sorting (Price-based)', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Sort selection persists product prices/details (no data corruption) after sorting', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const backpackName = 'Sauce Labs Backpack';
    const backpackSlug = 'sauce-labs-backpack';

    // 1. Record the price shown for 'Sauce Labs Backpack' while sorted Name (A to Z).
    await expect(inventoryPage.priceByName(backpackName)).toHaveText('$29.99');

    // 2. Sort by "Price (high to low)", then locate the 'Sauce Labs Backpack' item card by its name text.
    await inventoryPage.sortBy('hilo');
    await expect(inventoryPage.priceByName(backpackName)).toHaveText('$29.99');

    // 3. Click 'Add to cart' on the 'Sauce Labs Backpack' item while in Price (high to low) order, then re-sort to "Price (low to high)".
    await inventoryPage.addProductToCart(backpackSlug);
    await inventoryPage.sortBy('lohi');
    await expect(inventoryPage.removeButton(backpackSlug)).toHaveText('Remove');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');
  });
});
