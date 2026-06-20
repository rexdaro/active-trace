## Why

La pantalla de login actual es funcional pero tiene un diseño pobre para una demo. Se necesita una interfaz moderna, atractiva y con registro público integrado para que cualquier persona pueda crear una cuenta como ALUMNO y explorar el sistema.

## What Changes

- **Rediseño completo de la pantalla de login**: diseño centrado, con branding institucional, animaciones suaves, inputs claros, botón llamativo, mensajes de error estilizados (no alerts).
- **Formulario de registro público**: email + contraseña + confirmar contraseña. Crea usuario con rol ALUMNO automáticamente.
- **Toggle Login / Registro**: misma pantalla, cambia entre formulario de login y registro.
- **Backend**: `POST /api/auth/register` (ya definido en C-25) se consume desde el frontend.
- **Redirección post-registro**: al registrarse exitosamente, muestra mensaje y redirige al login.

## Capabilities

### New Capabilities
- `login-ui`: Pantalla de login rediseñada con diseño moderno y registro integrado.

### Modified Capabilities
- (ninguna — no se modifican requirements de specs existentes, solo UI)

## Impact

- **Frontend**: Se reemplaza la pantalla de login actual (`LoginPage.tsx` o similar) por una nueva con diseño moderno más el formulario de registro.
- **Backend**: Consume `POST /api/auth/register` (creado en C-25) y `POST /api/auth/login` (ya existente). No requiere cambios en backend.
- **Estilos**: Se agregan/actualizan estilos CSS para el nuevo diseño. Idealmente Tailwind o CSS modules.
- **Tests**: Tests de componente para login y registro, tests de integración con mocks de API.
