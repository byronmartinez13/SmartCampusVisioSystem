import { test, expect } from '@playwright/test';

test('registro, persistencia, perfil, cambio de contraseña y cierre de sesión', async ({ page }) => {
  const email = `browser-${Date.now()}@example.edu`;
  const password = 'Browser-Test!8926';
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login$/);
  await page.getByRole('link', { name: 'Registrarse', exact: true }).click();
  await page.getByLabel('Nombre', { exact: true }).fill('Usuario de prueba');
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  await expect(page.getByText('Aún no hay análisis esta semana')).toBeVisible();
  await page.screenshot({ path: '../tmp/dashboard-desktop.png', fullPage: true, animations: 'disabled' });
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Configuración' }).click();
  await page.getByLabel('Nombre', { exact: true }).fill('Perfil actualizado');
  await page.getByRole('button', { name: 'Guardar perfil' }).click();
  await expect(page.getByRole('status')).toHaveText('Perfil actualizado correctamente.');
  await page.getByLabel('Contraseña actual', { exact: true }).fill(password);
  await page.getByLabel('Nueva contraseña', { exact: true }).fill('New-Browser!9872');
  await page.getByLabel('Confirmar contraseña', { exact: true }).fill('New-Browser!9872');
  await page.getByRole('button', { name: 'Actualizar contraseña' }).click();
  await expect(page.getByRole('status')).toHaveText('Contraseña actualizada correctamente.');
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Inicio de sesión' })).toBeVisible();
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Correo o contraseña incorrectos.');
  await page.getByLabel('Contraseña', { exact: true }).fill('New-Browser!9872');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByText('Perfil actualizado', { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Abrir menú', exact: true }).click();
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: '../tmp/dashboard-mobile.png', fullPage: true, animations: 'disabled' });
});

test('recuperación y validación de enlace inválido', async ({ page }) => {
  await page.goto('/login');
  await page.getByRole('link', { name: '¿Olvidaste tu contraseña?' }).click();
  await page.getByLabel('Correo electrónico').fill('unknown@example.edu');
  await page.getByRole('button', { name: 'Enviar enlace' }).click();
  await expect(page.getByRole('status')).toContainText('Si existe una cuenta');
  await page.goto('/restablecer?uid=invalid&token=invalid');
  await page.getByLabel('Contraseña', { exact: true }).fill('Reset-Test!7129');
  await page.getByLabel('Confirmar contraseña', { exact: true }).fill('Reset-Test!7129');
  await page.getByRole('button', { name: 'Restablecer contraseña', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('no es válido');
});

test('login móvil accesible y sin desbordamiento horizontal', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Inicio de sesión' })).toBeVisible();
  await page.getByLabel('Contraseña', { exact: true }).fill('Visible!1234');
  await page.getByRole('button', { name: 'Mostrar contraseña', exact: true }).click();
  await expect(page.getByLabel('Contraseña', { exact: true })).toHaveAttribute('type', 'text');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: '../tmp/login-mobile.png', fullPage: true });
});
