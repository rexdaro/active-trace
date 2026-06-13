import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface DashboardStats {
  materias: number;
  atrasados: number;
  comunicacionesPendientes: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/materias').catch(() => ({ data: [] })),
      api.get('/api/v1/analisis/atrasados').catch(() => ({ data: [] })),
      api.get('/api/v1/comunicaciones').catch(() => ({ data: [] })),
    ])
      .then(([materiasRes, atrasadosRes, comunicacionesRes]) => {
        const materias = Array.isArray(materiasRes.data)
          ? materiasRes.data.length
          : materiasRes.data.total ?? 0;
        const atrasados = Array.isArray(atrasadosRes.data)
          ? atrasadosRes.data.length
          : atrasadosRes.data.total ?? 0;
        const comunicaciones = Array.isArray(comunicacionesRes.data)
          ? comunicacionesRes.data
          : [];
        setStats({
          materias,
          atrasados,
          comunicacionesPendientes: comunicaciones.filter(
            (c: { estado?: string }) => c.estado === 'pendiente'
          ).length,
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Acciones rápidas</h2>
        <div className="quick-actions">
          <Link to="/calificaciones" className="btn btn-primary">
            Importar calificaciones
          </Link>
          <Link to="/atrasados" className="btn btn-ghost">
            Ver atrasados
          </Link>
          <Link to="/comunicaciones" className="btn btn-ghost">
            Enviar comunicación
          </Link>
        </div>
      </div>
    </div>
  );
}
