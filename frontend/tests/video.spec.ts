import { test, expect } from '@playwright/test';
import { resolve } from 'node:path';

test('video: cargar, procesar con YOLO real, recargar, guardar y descargar resultados', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill('e2e-admin@example.edu');
  await page.getByLabel('Contraseña', { exact: true }).fill('Only-E2E!92741');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  const csrf = (await (await page.request.get('/api/auth/csrf/')).json()).csrfToken;
  const response = await page.request.post('/api/classrooms/', {
    headers: { 'X-CSRFToken': csrf },
    data: { name: `Video E2E ${Date.now()}`, kind: 'classroom', capacity: 10 },
  });
  expect(response.status()).toBe(201);
  const room = await response.json();
  await page.goto('/analisis');
  await page.getByRole('link', { name: 'Cargar video', exact: true }).click();
  await page.getByLabel('Aula o laboratorio', { exact: true }).selectOption(String(room.id));
  await page.getByLabel('Tipo de actividad').selectOption('practice');
  await page.getByLabel('Archivo de video').setInputFiles(resolve('tests/fixtures/empty-room.mp4'));
  await expect(page.getByRole('button', { name: 'Iniciar análisis' })).toBeEnabled();
  await page.screenshot({ path: '../tmp/video-upload-desktop.png', fullPage: true });
  await page.getByRole('button', { name: 'Iniciar análisis' }).click();
  await expect(page).toHaveURL(/\/analisis\/[a-f0-9-]+$/);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Resultado del análisis', exact: true })).toBeVisible({ timeout: 90000 });
  await expect(page.getByText('No disponible', { exact: true })).toBeVisible();
  await expect(page.getByText('yolo11n.pt', { exact: true })).toBeVisible();
  await expect(page.getByAltText('Fotograma del video con las detecciones de personas y monitores marcadas')).toBeVisible();
  await expect(page.getByText('Monitores · máximo detectado', { exact: true })).toBeVisible();
  expect(await page.locator('.analysis-preview').evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true);
  await page.getByRole('button', { name: 'Guardar resultado', exact: true }).click();
  await expect(page.getByText('Resultado guardado en el dashboard y la actividad del aula.')).toBeVisible();
  await page.reload();
  await expect(page.getByText('Resultado guardado en el dashboard y la actividad del aula.')).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar datos JSON' }).click();
  expect((await download).suggestedFilename()).toMatch(/^analisis-.*\.json$/);
  await expect.poll(() => page.locator('.analysis-preview').evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '../tmp/video-result-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../tmp/video-result-mobile.png', fullPage: true });
});
