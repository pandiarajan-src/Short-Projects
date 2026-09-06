import { Page, Locator } from '@playwright/test';
import { ItemListPage } from './ItemListPage';

export type SortOption = 'az' | 'za' | 'lohi' | 'hilo';

export class InventoryPage extends ItemListPage {
  readonly sortDropdown: Locator;

  constructor(page: Page) {
    super(page);
    this.sortDropdown = page.locator('[data-test="product-sort-container"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('https://www.saucedemo.com/inventory.html');
  }

  async sortBy(value: SortOption): Promise<void> {
    await this.sortDropdown.selectOption(value);
  }

  addToCartButton(slug: string): Locator {
    return this.page.locator(`[data-test="add-to-cart-${slug}"]`);
  }

  removeButton(slug: string): Locator {
    return this.page.locator(`[data-test="remove-${slug}"]`);
  }

  async addProductToCart(slug: string): Promise<void> {
    await this.addToCartButton(slug).click();
  }

  async removeProductFromCart(slug: string): Promise<void> {
    await this.removeButton(slug).click();
  }

  productLink(name: string): Locator {
    return this.rowByName(name).getByRole('link', { name, exact: true });
  }
}
