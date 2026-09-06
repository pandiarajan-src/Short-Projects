import { Page, Locator } from '@playwright/test';
import { ItemListPage } from './ItemListPage';

export class CartPage extends ItemListPage {
  readonly continueShoppingButton: Locator;
  readonly checkoutButton: Locator;

  constructor(page: Page) {
    super(page);
    this.continueShoppingButton = page.locator('[data-test="continue-shopping"]');
    this.checkoutButton = page.locator('[data-test="checkout"]');
  }

  removeButton(slug: string): Locator {
    return this.page.locator(`[data-test="remove-${slug}"]`);
  }

  async removeItem(slug: string): Promise<void> {
    await this.removeButton(slug).click();
  }

  quantityByName(name: string): Locator {
    return this.rowByName(name).locator('[data-test="item-quantity"]');
  }

  productLink(name: string): Locator {
    return this.rowByName(name).getByRole('link', { name, exact: true });
  }

  async continueShopping(): Promise<void> {
    await this.continueShoppingButton.click();
  }

  async checkout(): Promise<void> {
    await this.checkoutButton.click();
  }
}
