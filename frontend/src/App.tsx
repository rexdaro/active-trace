import { Routes, Route } from 'react-router-dom'
import AuthPage from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import RoleRoute from './components/RoleRoute'
import AppLayout from './components/AppLayout'
import Dashboard from './pages/Dashboard'
import Calificaciones from './pages/Calificaciones'
import Atrasados from './pages/Atrasados'
import Comunicaciones from './pages/Comunicaciones'
import EquiposDocentes from './pages/EquiposDocentes'
import Avisos from './pages/Avisos'
import Tareas from './pages/Tareas'
import Encuentros from './pages/Encuentros'
import Coloquios from './pages/Coloquios'
import Liquidaciones from './pages/Liquidaciones'
import Facturas from './pages/Facturas'
import Salarios from './pages/Salarios'
import EstructuraAcademica from './pages/EstructuraAcademica'
import Auditoria from './pages/Auditoria'
import Usuarios from './pages/Usuarios'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />

          {/* Coloquios — reserva y gestión */}
          <Route element={<RoleRoute roles={['ALUMNO', 'PROFESOR', 'COORDINADOR', 'ADMIN']} />}>
            <Route path="/coloquios" element={<Coloquios />} />
          </Route>

          {/* PROFESOR / TUTOR */}
          <Route element={<RoleRoute roles={['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN']} />}>
            <Route path="/calificaciones" element={<Calificaciones />} />
            <Route path="/atrasados" element={<Atrasados />} />
            <Route path="/tareas" element={<Tareas />} />
            <Route path="/encuentros" element={<Encuentros />} />
          </Route>

          {/* PROFESOR / COORDINADOR / ADMIN */}
          <Route element={<RoleRoute roles={['PROFESOR', 'COORDINADOR', 'ADMIN']} />}>
            <Route path="/comunicaciones" element={<Comunicaciones />} />
          </Route>

          {/* COORDINADOR / ADMIN */}
          <Route element={<RoleRoute roles={['COORDINADOR', 'ADMIN']} />}>
            <Route path="/equipos" element={<EquiposDocentes />} />
          </Route>

          {/* FINANZAS / ADMIN */}
          <Route element={<RoleRoute roles={['FINANZAS', 'ADMIN']} />}>
            <Route path="/liquidaciones" element={<Liquidaciones />} />
            <Route path="/facturas" element={<Facturas />} />
            <Route path="/salarios" element={<Salarios />} />
          </Route>

          {/* AUDITORIA */}
          <Route element={<RoleRoute roles={['COORDINADOR', 'ADMIN', 'FINANZAS']} />}>
            <Route path="/auditoria" element={<Auditoria />} />
          </Route>

          {/* ADMIN only */}
          <Route element={<RoleRoute roles={['ADMIN']} />}>
            <Route path="/estructura" element={<EstructuraAcademica />} />
            <Route path="/usuarios" element={<Usuarios />} />
          </Route>

          {/* All authenticated — avisos */}
          <Route path="/avisos" element={<Avisos />} />
        </Route>
      </Route>
    </Routes>
  )
}
