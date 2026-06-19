## Context

El login actual es funcional pero visualmente pobre: fondo blanco, inputs sin estilo, botón genérico, sin branding. Para la demo necesitamos algo que cause buena impresión desde el primer contacto. Además, no hay registro público — solo existe el usuario seed creado en DB.

## Goals / Non-Goals

**Goals:**
- Pantalla de login con diseño moderno, centrado, con branding (logo + nombre de la institución).
- Formulario de registro público (email + password + confirmar) en la misma pantalla, con toggle Login/Registro.
- Mensajes de error y éxito estilizados (no alerts nativos).
- Responsive: se ve bien en desktop y mobile.
- Transiciones suaves entre login y registro.

**Non-Goals:**
- No se rediseñan otras páginas — solo la pantalla de login/auth.
- No se agrega 2FA enrollment al registro (sigue siendo opcional post-login).
- No se toca el backend para este cambio (solo consume endpoints existentes de C-25).

## Decisions

### Decisión 1: Toggle en misma página vs páginas separadas
- **Opción A**: Login y registro en la misma página con toggle/tab.
- **Opción B**: Páginas separadas (ruta `/login` y `/register`).
- **Decisión**: **Opción A**. Más limpio para la demo, menos navegación, el usuario ve ambas opciones en un solo lugar. Se implementa con un estado `isRegistering` que cambia el formulario.

### Decisión 2: Diseño visual
- Diseño centrado, card sobre fondo con gradient suave o patrón sutil.
- Inputs con borde redondeado, placeholder visible, icono decorativo opcional.
- Botón primary con color institucional, hover effect.
- Logo institucional arriba del card (se puede usar un placeholder SVG).
- Transición CSS fade/slide al toggle entre login y registro.

### Decisión 3: Manejo de errores
- Errores del backend (401, 409, 422) se muestran como texto rojo dentro del card, no como alert.
- Éxito de registro muestra mensaje verde y redirige a login automáticamente tras 2 segundos.

## Risks / Trade-offs

- **[Risk] Diseño demasiado genérico**: sin un logo/branding real, puede verse como template.
  → **Mitigación**: usar placeholder institucional + esquema de colores profesional (azul oscuro + acento).
- **[Risk] Registro sin verificación de email**: para demo no hay problema, pero en producción requeriría confirmación.
  → **Aceptado**: es demo, no producción.
