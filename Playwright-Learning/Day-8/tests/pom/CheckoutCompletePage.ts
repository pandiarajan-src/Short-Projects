import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class CheckoutCompletePage extends BasePage {
  readonly completeHeader: Locator;
  readonly completeText: Locator;
  readonly ponyExpressImage: Locator;
  readonly backToProductsButton: Locator;
  readonly generatePdfOrderButton: Locator;

  constructor(page: Page) {
    super(page);
    this.completeHeader = page.locator('[data-test="complete-header"]');
    this.completeText = page.locator('[data-test="complete-text"]');
    this.ponyExpressImage = page.locator('[data-test="pony-express"]');
    this.backToProductsButton = page.locator('[data-test="back-to-products"]');
    this.generatePdfOrderButton = page.getByRole('button', { name: 'Generate PDF order' });
  }

  async backToProducts(): Promise<void> {
    await this.backToProductsButton.click();
  }
}
