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

  test('Sort products by Price (high to low)', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);

    // 1. Select the option "Price (high to low)" (value 'hilo') from [data-test="product-sort-container"].
    await inventoryPage.sortBy('hilo');
    await expect(inventoryPage.sortDropdown).toHaveValue('hilo');

    // 2. Extract the text of every inventory-item-price element in DOM order and parse to numbers.
    const prices = await inventoryPage.getProductPrices();
    expect(prices).toEqual([49.99, 29.99, 15.99, 15.99, 9.99, 7.99]);

    // 3. Extract the text of every inventory-item-name element in DOM order.
    const names = await inventoryPage.getProductNames();
    expect(names[0]).toBe('Sauce Labs Fleece Jacket');
    expect(names[1]).toBe('Sauce Labs Backpack');
    expect(names.slice(2, 4).sort()).toEqual(
      ['Sauce Labs Bolt T-Shirt', 'Test.allTheThings() T-Shirt (Red)'].sort()
    );
    expect(names[4]).toBe('Sauce Labs Bike Light');
    expect(names[5]).toBe('Sauce Labs Onesie');
  });
});
