import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
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
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calificaciones" element={<Calificaciones />} />
          <Route path="/atrasados" element={<Atrasados />} />
          <Route path="/comunicaciones" element={<Comunicaciones />} />
          <Route path="/equipos" element={<EquiposDocentes />} />
          <Route path="/avisos" element={<Avisos />} />
          <Route path="/tareas" element={<Tareas />} />
          <Route path="/encuentros" element={<Encuentros />} />
          <Route path="/coloquios" element={<Coloquios />} />
          <Route path="/liquidaciones" element={<Liquidaciones />} />
          <Route path="/facturas" element={<Facturas />} />
          <Route path="/salarios" element={<Salarios />} />
          <Route path="/estructura" element={<EstructuraAcademica />} />
          <Route path="/auditoria" element={<Auditoria />} />
          <Route path="/usuarios" element={<Usuarios />} />
        </Route>
      </Route>
    </Routes>
  )
}
