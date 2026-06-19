## 1. Diseño Login

- [ ] 1.1 Crear componente `AuthPage` con toggle entre login y registro (estado `isRegistering`)
- [ ] 1.2 Diseñar card centrado con fondo decorativo (gradient/pattern), logo placeholder, título
- [ ] 1.3 Agregar estilos CSS: inputs redondeados, botón primary, colores institucionales, transiciones
- [ ] 1.4 Implementar formulario de login: email + password + botón "Iniciar sesión"
- [ ] 1.5 Implementar formulario de registro: email + password + confirmar + botón "Crear cuenta"
- [ ] 1.6 Agregar validación de formularios (campos requeridos, password match)
- [ ] 1.7 Agregar transición animada al toggle entre login y registro

## 2. Integración con API

- [ ] 2.1 Conectar formulario de login con `POST /api/auth/login` (endpoint existente)
- [ ] 2.2 Conectar formulario de registro con `POST /api/auth/register` (endpoint de C-25)
- [ ] 2.3 Mostrar errores del backend dentro del card (401, 409, 422)
- [ ] 2.4 Mostrar mensaje de éxito en registro y redirigir a login tras 2 segundos
- [ ] 2.5 Manejar loading state durante las peticiones

## 3. Responsive y pulido

- [ ] 3.1 Asegurar diseño responsive (mobile first)
- [ ] 3.2 Agregar favicon/logo institucional placeholder
- [ ] 3.3 Verificar que el login existente (con token) sigue funcionando después del cambio
