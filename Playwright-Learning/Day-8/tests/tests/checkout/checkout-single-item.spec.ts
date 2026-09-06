// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';
import { CheckoutStepTwoPage } from '../../pom/CheckoutStepTwoPage';
import { CheckoutCompletePage } from '../../pom/CheckoutCompletePage';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Checkout with a single item (minimum happy path)', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);
    const checkoutComplete = new CheckoutCompletePage(page);

    // 1. Add only 'Sauce Labs Bike Light' to the cart, open the cart, and click Checkout.
    await inventoryPage.addProductToCart('sauce-labs-bike-light');
    await inventoryPage.goToCart();
    await cartPage.checkout();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');

    // 2. Fill in valid First Name, Last Name, and Postal Code, then click Continue.
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepTwo.itemRows).toHaveCount(1);
    await expect(checkoutStepTwo.priceByName('Sauce Labs Bike Light')).toHaveText('$9.99');
    await expect(checkoutStepTwo.subtotalLabel).toHaveText('Item total: $9.99');
    await expect(checkoutStepTwo.taxLabel).toHaveText('Tax: $0.80');
    await expect(checkoutStepTwo.totalLabel).toHaveText('Total: $10.79');

    // 3. Click Finish.
    await checkoutStepTwo.finish();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-complete.html');
    await expect(checkoutComplete.completeHeader).toHaveText('Thank you for your order!');
  });
});
