// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';
import { CheckoutStepOnePage } from '../../pom/CheckoutStepOnePage';
import { CheckoutStepTwoPage } from '../../pom/CheckoutStepTwoPage';
import { CheckoutCompletePage } from '../../pom/CheckoutCompletePage';

const ALL_SLUGS = [
  'sauce-labs-backpack',
  'sauce-labs-bike-light',
  'sauce-labs-bolt-t-shirt',
  'sauce-labs-fleece-jacket',
  'sauce-labs-onesie',
  'test.allthethings()-t-shirt-(red)',
];

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Complete checkout successfully with valid information (happy path)', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);
    const checkoutStepOne = new CheckoutStepOnePage(page);
    const checkoutStepTwo = new CheckoutStepTwoPage(page);
    const checkoutComplete = new CheckoutCompletePage(page);

    // 1. Add 'Sauce Labs Backpack' and 'Sauce Labs Onesie' to the cart from the inventory page,
    // then click [data-test="shopping-cart-link"].
    await inventoryPage.addProductToCart('sauce-labs-backpack');
    await inventoryPage.addProductToCart('sauce-labs-onesie');
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(2);
    await expect(cartPage.shoppingCartBadge).toHaveText('2');

    // 2. Click [data-test="checkout"].
    await cartPage.checkout();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-one.html');
    await expect(checkoutStepOne.title).toHaveText('Checkout: Your Information');

    // 3. Fill firstName, lastName, and postalCode.
    await checkoutStepOne.fillInfo('Pandi', 'Rajan', '560001');
    await expect(checkoutStepOne.firstNameInput).toHaveValue('Pandi');
    await expect(checkoutStepOne.lastNameInput).toHaveValue('Rajan');
    await expect(checkoutStepOne.postalCodeInput).toHaveValue('560001');

    // 4. Click [data-test="continue"].
    await checkoutStepOne.continue();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-step-two.html');
    await expect(checkoutStepTwo.title).toHaveText('Checkout: Overview');
    await expect(checkoutStepTwo.itemRows).toHaveCount(2);
    await expect(checkoutStepTwo.priceByName('Sauce Labs Backpack')).toHaveText('$29.99');
    await expect(checkoutStepTwo.priceByName('Sauce Labs Onesie')).toHaveText('$7.99');
    await expect(checkoutStepTwo.page.locator('[data-test^="remove-"]')).toHaveCount(0);
    await expect(checkoutStepTwo.paymentInfoValue).toHaveText('SauceCard #31337');
    await expect(checkoutStepTwo.shippingInfoValue).toHaveText('Free Pony Express Delivery!');
    await expect(checkoutStepTwo.subtotalLabel).toHaveText('Item total: $37.98');
    await expect(checkoutStepTwo.taxLabel).toHaveText('Tax: $3.04');
    await expect(checkoutStepTwo.totalLabel).toHaveText('Total: $41.02');

    // 5. Click [data-test="finish"].
    await checkoutStepTwo.finish();
    await expect(page).toHaveURL('https://www.saucedemo.com/checkout-complete.html');
    await expect(checkoutComplete.completeHeader).toHaveText('Thank you for your order!');
    await expect(checkoutComplete.completeText).toHaveText(
      'Your order has been dispatched, and will arrive just as fast as the pony can get there!'
    );
    await expect(checkoutComplete.ponyExpressImage).toBeVisible();

    // 6. Click [data-test="back-to-products"] ('Back Home').
    await checkoutComplete.backToProducts();
    await expect(page).toHaveURL('https://www.saucedemo.com/inventory.html');
    await expect(inventoryPage.shoppingCartBadge).toHaveCount(0);
    for (const slug of ALL_SLUGS) {
      await expect(inventoryPage.addToCartButton(slug)).toHaveText('Add to cart');
    }
  });
});
