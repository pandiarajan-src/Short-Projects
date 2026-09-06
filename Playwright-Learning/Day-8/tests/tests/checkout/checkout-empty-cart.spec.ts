// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

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

  test('Attempting checkout with an empty cart still allows reaching the info form', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);

    // 1. Without adding any items, navigate directly to the cart page via [data-test="shopping-cart-link"].
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(0);
    await expect(cartPage.shoppingCartBadge).toHaveCount(0);

    // 2. Click [data-test="checkout"] on the empty cart.
    await cartPage.checkout();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');

    // 3. Fill in valid First Name, Last Name, and Postal Code and click Continue.
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepTwo.itemRows).toHaveCount(0);
    // Verified live application behavior: with zero items the overview shows an
    // "Item total: $0" line, and tax/total both display as $0.00.
    await expect(checkoutStepTwo.subtotalLabel).toHaveText('Item total: $0');
    await expect(checkoutStepTwo.taxLabel).toHaveText('Tax: $0.00');
    await expect(checkoutStepTwo.totalLabel).toHaveText('Total: $0.00');
  });
});
