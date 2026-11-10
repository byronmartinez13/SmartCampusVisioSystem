import { test, expect } from '@playwright/test';

test.use({ permissions: ['camera'], launchOptions: { args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] } });

test('cámara trasera solicitada y monitor recibe video real y conteos sin detener al emisor', async ({ page, context }) => {
  test.setTimeout(180000);
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill('e2e-admin@example.edu');
  await page.getByLabel('Contraseña', { exact: true }).fill('Only-E2E!92741');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  await page.goto('/analisis/en-vivo');
  await expect(page.getByLabel('Cámara preferida')).toHaveValue('environment');
  const room = page.getByLabel('Aula', { exact: true });
  await expect(room.locator('option')).not.toHaveCount(1);
  await room.selectOption(await room.locator('option').nth(1).getAttribute('value') as string);
  await page.getByRole('button', { name: 'Iniciar cámara', exact: true }).click();
  const link = page.getByLabel('Ver video y conteos en la laptop');
  await expect(link).toBeVisible();
  const url = await link.inputValue();
  const monitor = await context.newPage();
  await monitor.goto(url);
  await expect(monitor.getByRole('heading', { name: 'Video en vivo conectado', exact: true })).toBeVisible({ timeout: 30000 });
  await expect.poll(() => monitor.locator('video').evaluate((v: HTMLVideoElement) => v.videoWidth > 0 && v.readyState >= 2)).toBe(true);
  await expect(monitor.getByRole('status')).toContainText('Personas:', { timeout: 120000 });
  await monitor.getByRole('button', { name: 'Reconectar', exact: true }).click();
  await expect(monitor.getByRole('heading', { name: 'Video en vivo conectado', exact: true })).toBeVisible({ timeout: 30000 });
  await monitor.close();
  await expect(page.getByRole('button', { name: 'Detener sesión', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Detener sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Sesión completada', exact: true })).toBeVisible({ timeout: 15000 });
  const ended = await context.newPage();
  await ended.goto(url);
  await expect(ended.getByText('La sesión ya no está activa.')).toBeVisible();
  await ended.close();
});
