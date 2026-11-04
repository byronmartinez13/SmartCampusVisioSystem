import { test, expect, type Page } from '@playwright/test';

async function login(page: Page, role = 'admin') {
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(`e2e-${role}@example.edu`);
  await page.getByLabel('Contraseña', { exact: true }).fill('Only-E2E!92741');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
}

test('aulas: crear, validar capacidad, editar, filtrar y conservar cambios', async ({ page }) => {
  const name = `Laboratorio E2E ${Date.now()}`;
  await login(page);
  await page.getByRole('link', { name: 'Aulas', exact: true }).click();
  await page.getByRole('link', { name: 'Nueva Aula/Laboratorio' }).click();
  await page.getByLabel('Nombre', { exact: true }).fill(name);
  await page.getByLabel('Tipo', { exact: true }).selectOption('lab');
  await page.getByLabel('Capacidad declarada', { exact: true }).fill('30');
  await page.getByLabel('Ubicación', { exact: true }).fill('Bloque A, planta 1');
  await page.getByLabel('Equipamiento (separado por comas)', { exact: true }).fill('Computadores, Proyector');
  await page.getByLabel('Cámara', { exact: true }).selectOption('usb');
  await page.getByLabel('Identificador de cámara', { exact: true }).fill('Cámara 01');
  await page.getByRole('button', { name: 'Añadir franja', exact: true }).click();
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  await expect(page.getByText('Pendiente de validación', { exact: true })).toBeVisible();
  await page.getByLabel('Puestos comprobados', { exact: true }).fill('28');
  await page.getByLabel('Observación', { exact: true }).fill('Conteo manual de puestos en el laboratorio');
  await page.getByRole('button', { name: 'Confirmar validación', exact: true }).click();
  await expect(page.getByText('Capacidad validada y registrada en el historial.')).toBeVisible();
  await expect(page.getByRole('cell', { name: '28', exact: true })).toBeVisible();
  await page.screenshot({ path: '../tmp/classroom-detail.png', fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: 'Editar Aula', exact: true }).click();
  await page.getByLabel('Capacidad declarada', { exact: true }).fill('31');
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByText('Pendiente de validación', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Volver a aulas', exact: true }).click();
  await page.getByLabel('Buscar', { exact: true }).fill(name);
  await expect(page.getByRole('cell', { name: '31 puestos', exact: true })).toBeVisible();
  await page.getByLabel('Tipo', { exact: true }).selectOption('classroom');
  await expect(page.getByRole('heading', { name: 'No hay espacios para mostrar' })).toBeVisible();
  await page.getByLabel('Tipo', { exact: true }).selectOption('lab');
  await expect(page.getByRole('cell', { name: '31 puestos', exact: true })).toBeVisible();
  await page.screenshot({ path: '../tmp/classrooms-desktop.png', fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: '../tmp/classrooms-mobile.png', fullPage: true, animations: 'disabled' });
});

test('datos académicos: docentes, asignaturas, cursos y rechazo de conflictos', async ({ page }) => {
  const stamp = Date.now().toString();
  const teacher = `Docente ${stamp}`;
  const subject = `Asignatura ${stamp}`;
  const course = `Curso ${stamp}`;
  await login(page);
  await page.getByRole('link', { name: 'Datos académicos', exact: true }).click();
  await page.getByRole('link', { name: 'Docentes', exact: true }).click();
  await page.getByRole('link', { name: 'Nuevo docente', exact: true }).click();
  await page.getByLabel('Nombre', { exact: true }).fill(teacher);
  await page.getByLabel('Correo', { exact: true }).fill(`teacher-${stamp}@example.edu`);
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByRole('cell', { name: teacher, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Asignaturas', exact: true }).click();
  await page.getByRole('link', { name: 'Nueva asignatura', exact: true }).click();
  await page.getByLabel('Nombre', { exact: true }).fill(subject);
  await page.getByLabel('Código', { exact: true }).fill(`S-${stamp}`);
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByRole('cell', { name: subject, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Cursos', exact: true }).click();
  await page.getByRole('link', { name: 'Nuevo curso', exact: true }).click();
  await page.getByLabel('Código', { exact: true }).fill(`C-${stamp}`);
  await page.getByLabel('Nombre del curso', { exact: true }).fill(course);
  await page.getByLabel('Asignatura', { exact: true }).selectOption({ label: `S-${stamp} · ${subject}` });
  await page.getByLabel('Docente', { exact: true }).selectOption({ label: teacher });
  await page.getByLabel('Estudiantes matriculados', { exact: true }).fill('25');
  await page.getByRole('button', { name: 'Añadir franja', exact: true }).click();
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByRole('heading', { name: course, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Editar curso', exact: true }).click();
  await page.getByLabel('Estudiantes matriculados', { exact: true }).fill('27');
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByText('27', { exact: true })).toBeVisible();
  await page.screenshot({ path: '../tmp/course-detail.png', fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: 'Volver a cursos', exact: true }).click();
  await page.getByRole('link', { name: 'Nuevo curso', exact: true }).click();
  await page.getByLabel('Código', { exact: true }).fill(`CONFLICT-${stamp}`);
  await page.getByLabel('Nombre del curso', { exact: true }).fill('Curso incompatible');
  await page.getByLabel('Asignatura', { exact: true }).selectOption({ label: `S-${stamp} · ${subject}` });
  await page.getByLabel('Docente', { exact: true }).selectOption({ label: teacher });
  await page.getByRole('button', { name: 'Añadir franja', exact: true }).click();
  await page.getByRole('button', { name: 'Guardar', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('conflicto de horario');
  await expect(page.getByLabel('Nombre del curso', { exact: true })).toHaveValue('Curso incompatible');
  await page.getByRole('link', { name: 'Cancelar', exact: true }).click();
  await page.getByLabel('Buscar cursos', { exact: true }).fill(`C-${stamp}`);
  await expect(page.getByRole('cell', { name: '27', exact: true })).toBeVisible();
});

test('consulta: sin creación ni edición y prohibición en API', async ({ page }) => {
  await login(page, 'viewer');
  await page.getByRole('link', { name: 'Aulas', exact: true }).click();
  await expect(page.getByText('Tu cuenta tiene acceso de consulta.', { exact: false })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Nueva Aula/Laboratorio' })).toHaveCount(0);
  await page.goto('/aulas/nueva');
  await expect(page.getByText('Tu cuenta tiene acceso de consulta.', { exact: false })).toBeVisible();
  const csrf = await page.request.get('/api/auth/csrf/');
  const response = await page.request.post('/api/classrooms/', {
    headers: { 'X-CSRFToken': (await csrf.json()).csrfToken },
    data: { name: 'Intento no autorizado', capacity: 10 },
  });
  expect(response.status()).toBe(403);
});
