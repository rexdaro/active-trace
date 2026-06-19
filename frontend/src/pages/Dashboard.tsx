import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getCurrentUser, type User } from '../services/api';

interface DashboardStats {
  materias: number;
  atrasados: number;
  comunicacionesPendientes: number;
}

interface QuickAction {
  path: string;
  label: string;
  variant: 'btn-primary' | 'btn-ghost';
  roles: string[];
}

const ALL_ACTIONS: QuickAction[] = [
  { path: '/calificaciones', label: 'Importar calificaciones', variant: 'btn-primary', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/atrasados', label: 'Ver atrasados', variant: 'btn-ghost', roles: ['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/comunicaciones', label: 'Enviar comunicación', variant: 'btn-ghost', roles: ['PROFESOR', 'COORDINADOR', 'ADMIN'] },
  { path: '/avisos', label: 'Ver avisos', variant: 'btn-ghost', roles: [] },
  { path: '/coloquios', label: 'Reservar coloquio', variant: 'btn-ghost', roles: ['ALUMNO'] },
  { path: '/facturas', label: 'Mis facturas', variant: 'btn-ghost', roles: ['FINANZAS', 'ADMIN'] },
  { path: '/liquidaciones', label: 'Liquidaciones', variant: 'btn-ghost', roles: ['FINANZAS', 'ADMIN'] },
];

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/materias').catch(() => ({ data: [] })),
      api.get('/api/v1/analisis/monitor/general').catch(() => ({ data: { total: 0 } })),
      api.get('/api/v1/comunicaciones/estados').catch(() => ({ data: {} })),
      getCurrentUser().catch(() => null),
    ])
      .then(([materiasRes, monitorRes, estadosRes, userData]) => {
        const materias = Array.isArray(materiasRes.data)
          ? materiasRes.data.length
          : (materiasRes.data.total ?? 0);

        const atrasados = monitorRes.data?.total ?? 0;

        const estadosData = estadosRes.data ?? {};
        const pendientes =
          (estadosData.pendiente ?? 0) +
          (estadosData.Pendiente ?? 0);

        setStats({ materias, atrasados, comunicacionesPendientes: pendientes });
        setUser(userData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const userRoles = user?.roles ?? [];

  const visibleActions = ALL_ACTIONS.filter(
    (a) => a.roles.length === 0 || a.roles.some((r) => userRoles.includes(r))
  );

  if (loading) return <div className="loading">Cargando dashboard...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.materias ?? 0}</div>
          <div className="stat-label">Materias</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.atrasados ?? 0}</div>
          <div className="stat-label">Alumnos atrasados</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.comunicacionesPendientes ?? 0}</div>
          <div className="stat-label">Comunicaciones pendientes</div>
        </div>
      </div>

      {visibleActions.length > 0 && (
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Acciones rápidas</h2>
          <div className="quick-actions">
            {visibleActions.map((action) => (
              <Link key={action.path} to={action.path} className={`btn ${action.variant}`}>
                {action.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
