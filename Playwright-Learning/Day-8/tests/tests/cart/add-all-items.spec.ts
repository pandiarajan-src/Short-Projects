// spec: tests/saucedemo-sort-cart-checkout.plan.md
// seed: seed.spec.ts

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pom/LoginPage';
import { InventoryPage } from '../../pom/InventoryPage';
import { CartPage } from '../../pom/CartPage';

const ALL_PRODUCTS: { slug: string; name: string; price: string }[] = [
  { slug: 'sauce-labs-backpack', name: 'Sauce Labs Backpack', price: '$29.99' },
  { slug: 'sauce-labs-bike-light', name: 'Sauce Labs Bike Light', price: '$9.99' },
  { slug: 'sauce-labs-bolt-t-shirt', name: 'Sauce Labs Bolt T-Shirt', price: '$15.99' },
  { slug: 'sauce-labs-fleece-jacket', name: 'Sauce Labs Fleece Jacket', price: '$49.99' },
  { slug: 'sauce-labs-onesie', name: 'Sauce Labs Onesie', price: '$7.99' },
  { slug: 'test.allthethings()-t-shirt-(red)', name: 'Test.allTheThings() T-Shirt (Red)', price: '$15.99' },
];

test.describe('Shopping Cart Management', () => {
  test.beforeEach(async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('standard_user', 'secret_sauce');
  });

  test('Add all six items to the cart in one session', async ({ page }) => {
    const inventoryPage = new InventoryPage(page);
    const cartPage = new CartPage(page);

    // 1. Click every 'Add to cart' button on the inventory page for all 6 products.
    for (const product of ALL_PRODUCTS) {
      await inventoryPage.addProductToCart(product.slug);
    }
    await expect(inventoryPage.shoppingCartBadge).toHaveText('6');
    for (const product of ALL_PRODUCTS) {
      await expect(inventoryPage.removeButton(product.slug)).toHaveText('Remove');
    }

    // 2. Navigate to the cart page.
    await inventoryPage.goToCart();
    await expect(cartPage.itemRows).toHaveCount(6);
    let totalQuantity = 0;
    for (const product of ALL_PRODUCTS) {
      await expect(cartPage.rowByName(product.name)).toBeVisible();
      await expect(cartPage.priceByName(product.name)).toHaveText(product.price);
      const quantityText = await cartPage.quantityByName(product.name).textContent();
      totalQuantity += parseInt(quantityText ?? '0', 10);
    }
    expect(totalQuantity).toBe(6);
  });
});
