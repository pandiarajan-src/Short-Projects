// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts
//
// Note: The plan expected Cancel on checkout-step-two.html to navigate back to
// https://www.saucedemo.com/cart.html. Live verification against the app shows
// it actually navigates to https://www.saucedemo.com/inventory.html (the Products
// page) instead. This test asserts the actual, verified application behavior.

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';
import { CheckoutStepTwoPage } from '../../pom/CheckoutStepTwoPage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Cancel on checkout overview (step two) returns to the inventory page', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);

    // 1. Add an item to the cart, complete checkout-step-one.html with valid data, and reach
    // checkout-step-two.html (Overview).
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepTwo.rowByName('Sauce Labs Backpack')).toBeVisible();
    await expect(checkoutStepTwo.totalLabel).toBeVisible();

    // 2. Click [data-test="cancel"].
    await checkoutStepTwo.cancel();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    await expect(inventoryPage.shoppingCartBadge).toHaveText('1');
    await expect(inventoryPage.removeButton('sauce-labs-backpack')).toBeVisible();
  });
});
