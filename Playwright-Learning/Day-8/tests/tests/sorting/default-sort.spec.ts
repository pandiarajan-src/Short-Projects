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

  test('Default sort is Name (A to Z) on page load', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);

    // 1. After logging in via the seed flow, land on the inventory page.
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    await expect(inventoryPage.sortDropdown).toHaveValue('az');

    // 2. Read all product names in the inventory item list, in DOM order.
    const names = await inventoryPage.getProductNames();
    expect(names).toEqual([
      'Sauce Labs Backpack',
      'Sauce Labs Bike Light',
      'Sauce Labs Bolt T-Shirt',
      'Sauce Labs Fleece Jacket',
      'Sauce Labs Onesie',
      'Test.allTheThings() T-Shirt (Red)',
    ]);
  });
});
