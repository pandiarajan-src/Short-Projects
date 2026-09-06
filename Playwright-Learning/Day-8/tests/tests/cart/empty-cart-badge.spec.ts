// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';

test.describe('Shopping Cart Management', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Cart badge is absent when cart is empty on initial load', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);

    // 1. On the inventory page immediately after login, check for the cart badge element.
    await expect(inventoryPage.shoppingCartBadge).toHaveCount(0);
  });
});
