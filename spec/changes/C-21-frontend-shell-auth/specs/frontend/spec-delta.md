## ADDED Requirements

### Requirement: Frontend Shell
WHEN un usuario accede a la URL del sistema,
el sistema SHALL renderizar el shell de la aplicación (layout base).

### Requirement: Autenticación
WHEN el usuario intenta acceder a una ruta protegida sin sesión,
el sistema SHALL redirigir al usuario a la página de `/login`.

### Requirement: Login
WHEN un usuario ingresa credenciales válidas en `/login`,
el sistema SHALL autenticarlo y redirigirlo a la página de inicio.
