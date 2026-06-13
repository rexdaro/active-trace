import { useEffect, useState } from 'react';
import api from '../services/api';

interface Metricas {
  accionesPorDia: number;
  comunicacionesPorDocente: number;
  ultimasAcciones: Array<{
    id: number;
    usuario: string;
    accion: string;
    created_at: string;
  }>;
}

interface LogEntry {
  id: number;
  usuario: string;
  accion: string;
  materia_id?: number;
  detalle?: string;
  created_at: string;
}

export default function Auditoria() {
  const [activeTab, setActiveTab] = useState<'panel' | 'log'>('panel');
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loadingMetricas, setLoadingMetricas] = useState(false);
  const [loadingLog, setLoadingLog] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [materiaId, setMateriaId] = useState('');
  const [usuarioId, setUsuarioId] = useState('');
  const [accion, setAccion] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (activeTab === 'panel') loadMetricas();
    else loadLog();
  }, [activeTab]);

  async function loadMetricas() {
    setLoadingMetricas(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/auditoria/metricas');
      setMetricas(res.data);
    } catch {
      setError('Error al cargar métricas');
    } finally {
      setLoadingMetricas(false);
    }
  }

  async function loadLog() {
    setLoadingLog(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page };
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;
      if (materiaId) params.materia_id = materiaId;
      if (usuarioId) params.usuario_id = usuarioId;
      if (accion) params.accion = accion;
      const res = await api.get('/api/v1/auditoria/log', { params });
      const data = res.data;
      setLogs(Array.isArray(data) ? data : data.items ?? []);
      setTotalPages(data.totalPages ?? data.total_pages ?? 1);
    } catch {
      setError('Error al cargar log de auditoría');
    } finally {
      setLoadingLog(false);
    }
  }

  function handleFilter(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadLog();
  }

  return (
    <div>
      <div className="page-header">
        <h1>Auditoría</h1>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="tabs">
        <button className={`tab ${activeTab === 'panel' ? 'active' : ''}`} onClick={() => setActiveTab('panel')}>Panel</button>
        <button className={`tab ${activeTab === 'log' ? 'active' : ''}`} onClick={() => setActiveTab('log')}>Log</button>
      </div>

      {activeTab === 'panel' && (
        <>
          {loadingMetricas ? (
            <div className="loading">Cargando métricas...</div>
          ) : metricas ? (
            <>
              <div className="card-grid">
                <div className="stat-card">
                  <div className="stat-value">{metricas.accionesPorDia}</div>
                  <div className="stat-label">Acciones por día</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{metricas.comunicacionesPorDocente}</div>
                  <div className="stat-label">Comunicaciones por docente</div>
                </div>
              </div>

              <div className="card">
                <h2 style={{ marginBottom: '1rem' }}>Últimas acciones</h2>
                {metricas.ultimasAcciones.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Usuario</th>
                          <th>Acción</th>
                          <th>Fecha</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metricas.ultimasAcciones.map((a) => (
                          <tr key={a.id}>
                            <td>{a.usuario}</td>
                            <td>{a.accion}</td>
                            <td>{new Date(a.created_at).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-muted)' }}>Sin acciones registradas.</p>
                )}
              </div>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No se pudieron cargar las métricas.</p>
          )}
        </>
      )}

      {activeTab === 'log' && (
        <>
          <div className="card">
            <form onSubmit={handleFilter}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Fecha desde</label>
                  <input type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Fecha hasta</label>
                  <input type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Materia ID</label>
                  <input type="number" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} placeholder="ID materia" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Usuario ID</label>
                  <input type="number" value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} placeholder="ID usuario" />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Acción</label>
                  <input type="text" value={accion} onChange={(e) => setAccion(e.target.value)} placeholder="Ej: login, create" />
                </div>
              </div>
              <button className="btn btn-primary" type="submit">Filtrar</button>
            </form>
          </div>

          <div className="card">
            {loadingLog ? (
              <div className="loading">Cargando...</div>
            ) : logs.length > 0 ? (
              <>
                <div style={{ overflowX: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Acción</th>
                        <th>Detalle</th>
                        <th>Materia</th>
                        <th>Fecha</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((l) => (
                        <tr key={l.id}>
                          <td>{l.usuario}</td>
                          <td>{l.accion}</td>
                          <td>{l.detalle || '—'}</td>
                          <td>{l.materia_id || '—'}</td>
                          <td>{new Date(l.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {totalPages > 1 && (
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginTop: '1rem' }}>
                    <button
                      className="btn btn-ghost"
                      disabled={page <= 1}
                      onClick={() => { setPage((p) => p - 1); loadLog(); }}
                    >
                      Anterior
                    </button>
                    <span style={{ alignSelf: 'center', fontSize: '0.875rem' }}>
                      Página {page} de {totalPages}
                    </span>
                    <button
                      className="btn btn-ghost"
                      disabled={page >= totalPages}
                      onClick={() => { setPage((p) => p + 1); loadLog(); }}
                    >
                      Siguiente
                    </button>
                  </div>
                )}
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No hay registros de auditoría.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
