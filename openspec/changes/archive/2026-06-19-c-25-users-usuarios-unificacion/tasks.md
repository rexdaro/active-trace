## 1. Modelo Unificado

- [ ] 1.1 Unificar modelo `User` en `app/models/user.py`: agregar campos de `Usuario` (dni, cuil, cbu, nombre, datos_fiscales, datos_bancarios, regional, modalidad_cobro) manteniendo cifrado para PII
- [ ] 1.2 Actualizar schemas en `app/schemas/usuario.py` para reflejar el modelo unificado
- [ ] 1.3 Crear migración Alembic: agregar columnas a `users`, migrar datos desde `usuarios`, eliminar tabla `usuarios`
- [ ] 1.4 Eliminar modelo `Usuario` y referencias obsoletas

## 2. Refactorizar Routers

- [ ] 2.1 Actualizar `app/routers/auth.py` para usar el modelo `User` unificado (login, refresh, 2FA)
- [ ] 2.2 Actualizar `app/routers/admin.py` para usar el modelo unificado en creación de usuarios
- [ ] 2.3 Actualizar `app/routers/usuarios.py` para usar el modelo unificado en listar/crear/asignar roles
- [ ] 2.4 Actualizar `app/routers/perfil.py` para usar el modelo unificado
- [ ] 2.5 Actualizar `app/routers/equipos.py` y `app/routers/asignaciones.py` si referencian `Usuario`
- [ ] 2.6 Actualizar cualquier otro router que importe `User` o `Usuario`

## 3. Refactorizar Services y Core

- [ ] 3.1 Actualizar `app/core/rbac.py` y `app/core/security.py` si referencian modelos viejos
- [ ] 3.2 Actualizar services que usen `Usuario` (buscar referencias con grep)

## 4. Endpoints de Admin

- [ ] 4.1 Implementar `POST /api/v1/usuarios` (admin crea usuario con rol opcional)
- [ ] 4.2 Implementar `PUT /api/v1/usuarios/{id}/roles` y `DELETE /api/v1/usuarios/{id}/roles`
- [ ] 4.3 Implementar `POST /api/auth/register` (registro público solo ALUMNO)

## 5. Tests

- [ ] 5.1 Actualizar tests existentes que crean `User` o `Usuario`
- [ ] 5.2 Agregar tests para `POST /api/v1/usuarios` (admin crea, email duplicado, rol inválido)
- [ ] 5.3 Agregar tests para `POST /api/auth/register` (registro exitoso, email duplicado)
- [ ] 5.4 Agregar tests para asignación/remoción de roles
- [ ] 5.5 Verificar que migración de datos legacy funciona
