// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Cancel on checkout step one returns to cart page', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);

    // 1. Add an item to the cart and proceed to checkout-step-one.html.
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');
    await expect(checkoutStepOne.firstNameInput).toBeVisible();

    // 2. Optionally fill in some field values, then click [data-test="cancel"].
    await checkoutStepOne.firstNameInput.fill('Pandi');
    await checkoutStepOne.lastNameInput.fill('Rajan');
    await checkoutStepOne.cancel();
    await expect(page).toHaveURL('https://www.saucedemo.com/cart.html');
    await expect(cartPage.rowByName('Sauce Labs Backpack')).toBeVisible();
  });
});
