import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { getCurrentUser, type User } from '../services/api';

type Role = string;

interface MenuItem {
  path: string;
  label: string;
  roles: Role[];  // empty = visible to all
}

const menuItems: MenuItem[] = [
  { path: '/', label: 'Dashboard', roles: [] },
  { path: '/calificaciones', label: 'Calificaciones', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/atrasados', label: 'Atrasados', roles: ['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/comunicaciones', label: 'Comunicaciones', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/equipos', label: 'Equipos docentes', roles: ['COORDINADOR', 'ADMIN'] },
  { path: '/avisos', label: 'Avisos', roles: [] },
  { path: '/tareas', label: 'Tareas', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/encuentros', label: 'Encuentros', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/coloquios', label: 'Coloquios', roles: ['ALUMNO', 'PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/liquidaciones', label: 'Liquidaciones', roles: ['FINANZAS', 'ADMIN'] },
  { path: '/facturas', label: 'Facturas', roles: ['FINANZAS', 'ADMIN'] },
  { path: '/salarios', label: 'Salarios', roles: ['FINANZAS', 'ADMIN'] },
  { path: '/estructura', label: 'Estructura', roles: ['ADMIN'] },
  { path: '/auditoria', label: 'Auditoría', roles: ['COORDINADOR', 'ADMIN', 'FINANZAS'] },
  { path: '/usuarios', label: 'Usuarios', roles: ['ADMIN'] },
];

function canSeeItem(item: MenuItem, userRoles: Role[]): boolean {
  if (item.roles.length === 0) return true;          // visible to all
  return item.roles.some((r) => userRoles.includes(r));
}

export default function AppLayout() {
  const [user, setUser] = useState<User | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setError('Error al cargar usuario'));
  }, []);

  function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    navigate('/login');
  }

  const userRoles = user?.roles ?? [];

  return (
    <div className="app-layout">
      <button
        className="sidebar-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? '✕' : '☰'}
      </button>

      <div
        className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">trace</div>

        <nav className="sidebar-nav">
          {menuItems.filter((item) => canSeeItem(item, userRoles)).map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => (isActive ? 'active' : '')}
              onClick={() => setSidebarOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {error && <div className="user-info error">{error}</div>}
          {user && (
            <div className="user-info">
              <div>{user.nombre}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{user.email}</div>
            </div>
          )}
          <button className="logout-btn" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
