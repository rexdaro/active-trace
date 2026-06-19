## Context

Actualmente el proyecto maneja dos entidades separadas para personas:

- **`User`** (`users`): autenticación, email, password hasheado, 2FA, roles vía `user_roles`.
- **`Usuario`** (`usuarios`): datos fiscales/PII cifrados (DNI, CUIL, CBU), nombre, datos bancarios.

Esto obliga a mantener dos tablas sincronizadas, duplica lógica en services, y complica el registro de nuevos usuarios. Para la demo, unificar simplifica todo: un solo modelo, un solo CRUD, registro público y admin en un mismo lugar.

## Goals / Non-Goals

**Goals:**
- Una sola tabla `users` con todos los campos de auth + PII + datos personales.
- Migración de datos existentes sin pérdida.
- Registro público (solo rol ALUMNO).
- Admin puede crear usuarios con cualquier rol desde `POST /api/v1/usuarios`.
- Todos los routers, schemas, services y tests actualizados.

**Non-Goals:**
- No se cambia la lógica de asignaciones, calificaciones ni otros módulos de dominio que referencian `User`/`Usuario` por FK — solo se actualiza la referencia al modelo unificado.
- No se agregan nuevas funcionalidades de perfil más allá de lo necesario para la demo.
- No se toca la lógica de 2FA (sigue igual, solo se mueve el campo a la tabla unificada).

## Decisions

### Decisión 1: Mantener el nombre `User` para la tabla unificada

- **Opción A**: Crear nueva tabla `UserUnified` y mapear.
- **Opción B**: Migrar todo a la tabla `users` existente, agregando columnas de `usuarios`.
- **Decisión**: **Opción B**. La tabla `users` ya es la referencia en la mayoría de relaciones (FKs en `user_roles`, `refresh_tokens`, `asignaciones`, etc.). Es menos riesgoso agregar columnas a `users` que recrear FKs. La tabla `usuarios` se elimina tras migrar sus datos.

### Decisión 2: Cifrado de PII en la tabla unificada

- Los campos `dni`, `cuil`, `cbu`, `email` del modelo `Usuario` se cifraban con AES-256. En la tabla unificada, `email` ya existe en texto plano (para login). DNI, CUIL y CBU se mantienen cifrados con el mismo mecanismo.
- **Decisión**: `email` se queda en texto plano (como está en `users`). DNI, CUIL, CBU se migran con su cifrado actual a la nueva columna en `users`. No se cambia el schema de cifrado.

### Decisión 3: Migración de datos

- Se crea una migración Alembic que:
  1. Agrega columnas nuevas a `users` (`dni`, `cuil`, `cbu`, `nombre`, `datos_fiscales`, `datos_bancarios`, `regional`, `modalidad_cobro`).
  2. Copia datos de `usuarios` a `users` haciendo JOIN por `tenant_id` y `email` (con descifrado para el match).
  3. Elimina la tabla `usuarios`.

## Risks / Trade-offs

- **[Risk] Match imperfecto entre `usuarios` y `users`**: puede haber usuarios en `users` sin registro en `usuarios` o viceversa. 
  → **Mitigación**: LEFT JOIN, los campos faltantes quedan NULL. No hay datos críticos en juego.
- **[Risk] FKs apuntando a `users.id` ya existen**: al mantener la tabla `users`, las FKs existentes siguen funcionando sin cambios.
  → Sin riesgo.
- **[Risk] Cifrado de DNI/CUIL/CBU**: al mover los datos cifrados, la clave de cifrado sigue siendo la misma (ENCRYPTION_KEY). No hay riesgo de perder datos.
  → Sin riesgo.
