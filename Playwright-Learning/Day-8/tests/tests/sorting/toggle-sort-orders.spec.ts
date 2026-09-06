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

  test('Toggle between price sorts and back to name sort updates order each time', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const originalNames = await inventoryPage.getProductNames();

    // 1. Select "Price (low to high)" from the sort dropdown.
    await inventoryPage.sortBy('lohi');
    let prices = await inventoryPage.getProductPrices();
    expect(prices[0]).toBe(7.99);

    // 2. Select "Price (high to low)" from the sort dropdown without reloading the page.
    await inventoryPage.sortBy('hilo');
    prices = await inventoryPage.getProductPrices();
    expect(prices[0]).toBe(49.99);
    expect(await inventoryPage.getItemCount()).toBe(6);

    // 3. Select "Name (Z to A)" from the sort dropdown.
    await inventoryPage.sortBy('za');
    const zaNames = await inventoryPage.getProductNames();
    expect(zaNames[0]).toBe('Test.allTheThings() T-Shirt (Red)');
    expect(zaNames[zaNames.length - 1]).toBe('Sauce Labs Backpack');

    // 4. Select "Name (A to Z)" from the sort dropdown again.
    await inventoryPage.sortBy('az');
    const azNames = await inventoryPage.getProductNames();
    expect(azNames).toEqual(originalNames);
  });
});
