## Why

El proyecto tiene dos tablas separadas para representar usuarios: `users` (autenticación) y `usuarios` (datos fiscales/PII). Esto complica el registro, la gestión desde el frontend y la demo. Unificarlas en una sola entidad simplifica el modelo, permite el registro público y que el admin cree usuarios con roles desde la UI.

## What Changes

- **Unificar `users` + `usuarios`** en una sola tabla con todos los campos: email, password, DNI, CUIL, CBU, nombre, 2FA, timestamps. **BREAKING**
- Migrar datos existentes de ambas tablas a la unificada y eliminar tablas viejas.
- Refactorizar todos los routers, schemas, services y tests que referencian `User` o `Usuario` para que apunten a la nueva entidad.
- Agregar `POST /api/v1/usuarios` para que el admin cree usuarios con cualquier rol.
- Agregar `PUT /api/v1/usuarios/{id}/roles` para asignar/quitar roles.
- Mantener `GET /api/v1/usuarios` existente (ya creado en hotfix) actualizado al nuevo modelo.

## Capabilities

### New Capabilities
- `user-admin`: Creación de usuarios por admin con selección de roles, asignación/remoción de roles desde el frontend.

### Modified Capabilities
- `user-management`: El modelo de usuario cambia de dos tablas a una unificada. Se modifica el schema de la entidad y todos los endpoints que la utilizan.

## Impact

- **Modelos**: Se eliminan `User` y `Usuario`. Se crea `UserUnified` (o se renueva `User` como la tabla única).
- **Routers**: `auth.py`, `admin.py`, `usuarios.py`, `perfil.py`, `equipos.py`, `asignaciones.py` — todos los que importan `User` o `Usuario` requieren actualización.
- **Schemas**: `usuario.py` se fusiona con schemas de auth. Schemas de `Asignacion`, `Calificacion`, etc. referencian el nuevo modelo.
- **Services/Repositories**: Todos los que referencian `User` o `Usuario` deben actualizarse.
- **Tests**: Todos los tests que crean `User` o `Usuario` deben migrarse al nuevo modelo.
- **Base de datos**: Migración Alembic que crea la tabla unificada, migra datos y elimina las viejas.
- **Frontend**: El formulario de crear usuario en el panel admin (C-24) debe consumir `POST /api/v1/usuarios`.
