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

  test('Add a single item to the cart updates badge and button state', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const backpackSlug = 'sauce-labs-backpack';
    const backpackName = 'Sauce Labs Backpack';

    // 1. Click [data-test="add-to-cart-sauce-labs-backpack"] on the inventory page.
    await inventoryPage.addProductToCart(backpackSlug);
    await expect(inventoryPage.removeButton(backpackSlug)).toHaveText('Remove');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');

    // 2. Click [data-test="shopping-cart-link"] to open the cart page.
    await inventoryPage.goToCart();
    await expect(page).toHaveURL('https://www.saucedemo.com/cart.html');
    await expect(cartPage.itemRows).toHaveCount(1);
    await expect(cartPage.rowByName(backpackName)).toBeVisible();
    await expect(cartPage.quantityByName(backpackName)).toHaveText('1');
    await expect(cartPage.priceByName(backpackName)).toHaveText('$29.99');
  });
});
