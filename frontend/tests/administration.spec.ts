import { test, expect } from '@playwright/test';

test('configuración, reglas, roles y auditoría persisten con permisos', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill('e2e-admin@example.edu');
  await page.getByLabel('Contraseña', { exact: true }).fill('Only-E2E!92741');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  const original = await (await page.request.get('/api/settings/')).json();
  const users = await (await page.request.get('/api/auth/users/')).json();
  const viewer = users.find((u: { email: string }) => u.email === 'e2e-viewer@example.edu');
  try {
    await page.getByRole('link', { name: 'Configuración', exact: true }).click();
    await page.getByLabel('Confianza predeterminada del detector').fill('0.4');
    await page.getByRole('button', { name: 'Guardar configuración general' }).click();
    await expect(page.getByText('Configuración guardada. Se aplicará a los nuevos análisis.')).toBeVisible();
    await page.reload();
    await expect(page.getByLabel('Confianza predeterminada del detector')).toHaveValue('0.4');
    await page.screenshot({ path: '../tmp/settings-general.png', fullPage: true });
    await page.getByRole('link', { name: 'Reglas de asignación', exact: true }).click();
    const rules = await (await page.request.get('/api/assignment-rules/')).json();
    if (!rules.some((r: { kind: string }) => r.kind === 'preferred_kind')) {
      await page.getByLabel('Tipo de regla', { exact: true }).selectOption('preferred_kind');
      await page.getByLabel('Valor', { exact: true }).selectOption('lab');
      await page.getByRole('button', { name: 'Registrar regla', exact: true }).click();
    }
    await expect(page.getByRole('heading', { name: 'Preferencia de espacio', exact: true })).toBeVisible();
    await page.screenshot({ path: '../tmp/rules-desktop.png', fullPage: true });
    await page.goto('/administracion/usuarios');
    await page.getByLabel('Rol de E2E viewer', { exact: true }).selectOption('coordinator');
    await page.getByLabel('Motivo del cambio de E2E viewer', { exact: true }).fill('Prueba de coordinación del equipo');
    const card = page.locator('section').filter({ has: page.getByRole('heading', { name: 'E2E viewer', exact: true }) });
    await card.getByRole('checkbox', { name: 'Confirmo el cambio de acceso para esta cuenta' }).check();
    await card.getByRole('button', { name: 'Guardar acceso' }).click();
    await page.reload();
    await expect(page.getByLabel('Rol de E2E viewer', { exact: true })).toHaveValue('coordinator');
    await page.goto('/administracion/auditoria');
    await expect(page.getByRole('heading', { name: 'Acceso de usuario actualizado', exact: true }).first()).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: '../tmp/administration-mobile.png', fullPage: true });
  } finally {
    const csrf = (await (await page.request.get('/api/auth/csrf/')).json()).csrfToken;
    const headers = { 'X-CSRFToken': csrf };
    const current = await (await page.request.get('/api/settings/')).json();
    await page.request.patch('/api/settings/', { headers, data: { ...original, version: current.version } });
    await page.request.patch(`/api/auth/users/${viewer.id}/access/`, { headers, data: { role: viewer.role, is_active: true, note: 'Restaurar cuenta de pruebas' } });
    const rules = await (await page.request.get('/api/assignment-rules/')).json();
    const rule = rules.find((r: { kind: string }) => r.kind === 'preferred_kind');
    if (rule) await page.request.patch(`/api/assignment-rules/${rule.id}/`, { headers, data: { version: rule.version, active: false } });
  }
});
