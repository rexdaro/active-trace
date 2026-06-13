import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { getCurrentUser, type User } from '../services/api';

interface MenuItem {
  path: string;
  label: string;
  permission: string | null;
}

const menuItems: MenuItem[] = [
  { path: '/', label: 'Dashboard', permission: null },
  { path: '/calificaciones', label: 'Calificaciones', permission: 'calificaciones' },
  { path: '/atrasados', label: 'Atrasados', permission: 'atrasados' },
  { path: '/comunicaciones', label: 'Comunicaciones', permission: 'comunicaciones' },
  { path: '/equipos', label: 'Equipos docentes', permission: 'equipos' },
  { path: '/avisos', label: 'Avisos', permission: 'avisos' },
  { path: '/tareas', label: 'Tareas', permission: 'tareas' },
  { path: '/encuentros', label: 'Encuentros', permission: 'encuentros' },
  { path: '/coloquios', label: 'Coloquios', permission: 'coloquios' },
  { path: '/liquidaciones', label: 'Liquidaciones', permission: 'liquidaciones' },
  { path: '/facturas', label: 'Facturas', permission: 'facturas' },
  { path: '/salarios', label: 'Salarios', permission: 'salarios' },
  { path: '/estructura', label: 'Estructura', permission: 'estructura' },
  { path: '/auditoria', label: 'Auditoría', permission: 'auditoria' },
  { path: '/usuarios', label: 'Usuarios', permission: 'usuarios' },
];

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

  function hasPermission(permission: string | null): boolean {
    if (!permission) return true;
    if (!user) return false;
    return user.permissions.some((p) => p.startsWith(permission));
  }

  function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    navigate('/login');
  }

  const visibleItems = menuItems.filter((item) => hasPermission(item.permission));

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
          {visibleItems.map((item) => (
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
