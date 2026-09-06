import { test, expect } from '@playwright/test';

test('standard_user can add items to cart and checkout', async ({ page }) => {
  await page.goto('https://www.saucedemo.com/');

  // Login
  await page.getByPlaceholder('Username').fill('standard_user');
  await page.getByPlaceholder('Password').fill('secret_sauce');
  await page.getByRole('button', { name: 'Login' }).click();
  await expect(page).toHaveURL(/inventory\.html/);

  // Add items to cart
  await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
  await page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click();
  await expect(page.locator('.shopping_cart_badge')).toHaveText('2');

  // Go to cart and verify contents
  await page.locator('.shopping_cart_link').click();
  await expect(page).toHaveURL(/cart\.html/);
  await expect(page.getByRole('link', { name: 'Sauce Labs Backpack' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sauce Labs Bike Light' })).toBeVisible();

  // Checkout step one: customer information
  await page.locator('[data-test="checkout"]').click();
  await expect(page).toHaveURL(/checkout-step-one\.html/);
  await page.locator('[data-test="firstName"]').fill('Pandi');
  await page.locator('[data-test="lastName"]').fill('Rajan');
  await page.locator('[data-test="postalCode"]').fill('560001');
  await page.locator('[data-test="continue"]').click();

  // Checkout step two: overview
  await expect(page).toHaveURL(/checkout-step-two\.html/);
  await expect(page.getByText('Total: $43.18')).toBeVisible();
  await page.locator('[data-test="finish"]').click();

  // Order confirmation
  await expect(page).toHaveURL(/checkout-complete\.html/);
  await expect(page.getByRole('heading', { name: 'Thank you for your order!' })).toBeVisible();
});
