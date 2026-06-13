# Design: C-22-frontend-academico-docente

## Infrastructure
- React Router with routes: /login, / (dashboard), /calificaciones, /atrasados, /comunicaciones
- ProtectedRoute component: checks token, redirects to /login if missing
- AppLayout: sidebar with menu items filtered by permissions from /auth/me endpoint
- Shared API client at services/api.ts (existing, add refresh token interceptor)

## Pages
### Dashboard (/) 
- Summary cards: total materias, alumnos atrasados, comunicaciones pendientes
- Quick actions: importar calificaciones, ver atrasados

### Calificaciones (/calificaciones)
- Select materia dropdown -> carga data
- Tabla de calificaciones importadas
- Preview antes de importar
- Configurar umbral de aprobaciÃ³n

### Atrasados (/atrasados)
- Tabla de alumnos atrasados por materia
- Ranking de actividades aprobadas
- Reportes rÃ¡pidos (export)

### Comunicaciones (/comunicaciones)
- Preview de comunicaciÃ³n antes de enviar
- EnvÃ­o masivo a atrasados
- Tracking de estado de envÃ­os
