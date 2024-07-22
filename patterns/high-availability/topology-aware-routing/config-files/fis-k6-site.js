import { browser } from 'k6/browser';
import { parseHTML } from 'k6/html';
import { check } from 'k6';
import http from 'k6/http';

export const options = {
  scenarios: {
    browser: {
      executor: 'constant-vus',
      exec: 'browserTest',
      vus: 2,
      duration: '599s',
      options: {
        browser: {
          type: 'chromium',
        }
      }
    }
  }
};

export async function browserTest() {
  const page = await browser.newPage();

  await page.goto('http://URI/');
  const doc = parseHTML(await page.content());
  console.log(doc.find('body').text().replace(/(\r\n|\n|\r)/gm, " "));
}