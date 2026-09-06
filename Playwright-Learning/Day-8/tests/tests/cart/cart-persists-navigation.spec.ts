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

  test('Cart contents persist across navigation to inventory and back', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Add 'Sauce Labs Fleece Jacket' to the cart, navigate to the cart page, then click
    // [data-test="continue-shopping"] to go back to inventory.
    await inventoryPage.addProductToCart('sauce-labs-fleece-jacket');
    await inventoryPage.goToCart();
    await cartPage.continueShopping();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');
    await expect(inventoryPage.removeButton('sauce-labs-fleece-jacket')).toHaveText('Remove');

    // 2. Navigate to the cart page again via [data-test="shopping-cart-link"].
    await inventoryPage.goToCart();
    await expect(cartPage.rowByName('Sauce Labs Fleece Jacket')).toBeVisible();
    await expect(cartPage.quantityByName('Sauce Labs Fleece Jacket')).toHaveText('1');
    await expect(cartPage.priceByName('Sauce Labs Fleece Jacket')).toHaveText('$49.99');
  });
});
