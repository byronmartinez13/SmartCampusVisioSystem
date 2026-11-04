import { test, expect } from '@playwright/test';

test.use({ permissions: ['camera'], launchOptions: { args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] } });

test('cámara simulada con detector real: iniciar, analizar, detener y consultar', async ({ page }) => {
  test.setTimeout(240000);
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill('e2e-admin@example.edu');
  await page.getByLabel('Contraseña', { exact: true }).fill('Only-E2E!92741');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  const original = await (await page.request.get('/api/settings/')).json();
  const csrf = (await (await page.request.get('/api/auth/csrf/')).json()).csrfToken;
  const headers = { 'X-CSRFToken': csrf };
  const configured = await page.request.patch('/api/settings/', { headers, data: {
    version: original.version, record_live: true, auto_save: true, auto_pdf: true,
  } });
  expect(configured.ok()).toBe(true);
  try {
  await page.getByRole('link', { name: 'Análisis', exact: true }).click();
  await page.getByRole('link', { name: 'Abrir cámara' }).click();
  const select = page.getByLabel('Aula', { exact: true });
  await expect(select.locator('option')).not.toHaveCount(1);
  const value = await select.locator('option').nth(1).getAttribute('value');
  await select.selectOption(value!);
  await page.getByRole('checkbox', { name: /Grabar cámara para descargar localmente/ }).check();
  await page.getByRole('button', { name: 'Iniciar cámara' }).click();
  await expect(page.getByText(/Personas:.*Muestras:/)).toBeVisible({ timeout: 180000 });
  await page.getByRole('button', { name: 'Detener sesión' }).click();
  await expect(page.getByRole('link', { name: 'Ver resultado y guardar resumen' })).toBeVisible();
  expect(await page.locator('video').evaluate((el: HTMLVideoElement) => (el.srcObject as MediaStream).getTracks().every(t => t.readyState === 'ended'))).toBe(true);
  await page.screenshot({ path: '../tmp/live-desktop.png', fullPage: true });
  const recording = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Descargar grabación WebM' }).click();
  expect((await recording).suggestedFilename()).toMatch(/^camara-.*\.webm$/);
  const pdf = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Ver resultado y guardar resumen' }).click();
  expect((await pdf).suggestedFilename()).toMatch(/^analisis-.*\.pdf$/);
  await expect(page.getByText('Las muestras de la cámara no se conservan como imágenes.')).toBeVisible();
  await expect(page.getByText('Resultado guardado en el dashboard y la actividad del aula.')).toBeVisible();
  } finally {
    const current = await (await page.request.get('/api/settings/')).json();
    await page.request.patch('/api/settings/', { headers, data: { ...original, version: current.version } });
  }
});
