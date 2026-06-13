import { useEffect, useState } from 'react';
import api from '../services/api';

interface Convocatoria {
  id: number;
  materia: string;
  fecha: string;
  cupos: number;
  convocados: number;
  reservas: number;
  libres: number;
}

interface Metricas {
  convocados: number;
  reservas: number;
  libres: number;
}

export default function Coloquios() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [materiaId, setMateriaId] = useState('');
  const [fecha, setFecha] = useState('');
  const [cupos, setCupos] = useState('');

  const [metricas, setMetricas] = useState<Record<number, Metricas>>({});
  const [loadingMetricas, setLoadingMetricas] = useState<Record<number, boolean>>({});

  useEffect(() => {
    api
      .get('/api/v1/coloquios')
      .then((res) => setConvocatorias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar coloquios'))
      .finally(() => setLoading(false));
  }, []);

  function resetForm() {
    setMateriaId('');
    setFecha('');
    setCupos('');
  }

  async function handleCreate() {
    if (!materiaId || !fecha || !cupos) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/coloquios', {
        materia_id: Number(materiaId),
        fecha,
        cupos: Number(cupos),
      });
      setSuccess('Convocatoria creada');
      resetForm();
      setShowForm(false);
      const res = await api.get('/api/v1/coloquios');
      setConvocatorias(Array.isArray(res.data) ? res.data : []);
    } catch {
      setError('Error al crear convocatoria');
    }
  }

  async function handleImportar(id: number) {
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/api/v1/coloquios/${id}/importar`);
      setSuccess('Alumnos importados');
      const res = await api.get('/api/v1/coloquios');
      setConvocatorias(Array.isArray(res.data) ? res.data : []);
    } catch {
      setError('Error al importar alumnos');
    }
  }

  async function handleMetricas(id: number) {
    if (metricas[id]) {
      setMetricas((prev) => { const n = { ...prev }; delete n[id]; return n; });
      return;
    }
    setLoadingMetricas((prev) => ({ ...prev, [id]: true }));
    try {
      const res = await api.get(`/api/v1/coloquios/${id}/metricas`);
      setMetricas((prev) => ({ ...prev, [id]: res.data }));
    } catch {
      setError('Error al cargar métricas');
    } finally {
      setLoadingMetricas((prev) => ({ ...prev, [id]: false }));
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Coloquios</h1>
        <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); resetForm(); }}>
          {showForm ? 'Cancelar' : 'Nueva convocatoria'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div
          className="error-message"
          style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}
        >
          {success}
        </div>
      )}

      {showForm && (
        <div className="card" style={{ maxWidth: '500px' }}>
          <h3 style={{ marginBottom: '1rem' }}>Nueva convocatoria</h3>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Materia ID</label>
            <input type="number" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} placeholder="ID de materia" />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Fecha</label>
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Cupos</label>
            <input type="number" min={1} value={cupos} onChange={(e) => setCupos(e.target.value)} placeholder="Cantidad de cupos" />
          </div>

          <button className="btn btn-primary" onClick={handleCreate} disabled={!materiaId || !fecha || !cupos}>
            Crear convocatoria
          </button>
        </div>
      )}

      <div className="card">
        {convocatorias.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Materia</th>
                  <th>Fecha</th>
                  <th>Cupos</th>
                  <th>Convocados</th>
                  <th>Métricas</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {convocatorias.map((c) => (
                  <tr key={c.id}>
                    <td>{c.materia}</td>
                    <td>{new Date(c.fecha).toLocaleDateString()}</td>
                    <td>{c.cupos}</td>
                    <td>{c.convocados}</td>
                    <td>
                      <button
                        className="btn btn-ghost"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                        onClick={() => handleMetricas(c.id)}
                      >
                        {metricas[c.id] ? 'Ocultar' : 'Ver métricas'}
                      </button>
                      {loadingMetricas[c.id] && <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Cargando...</span>}
                      {metricas[c.id] && !loadingMetricas[c.id] && (
                        <div style={{ fontSize: '0.8rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                          Convocados: {metricas[c.id].convocados} | Reservas: {metricas[c.id].reservas} | Libres: {metricas[c.id].libres}
                        </div>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                        onClick={() => handleImportar(c.id)}
                      >
                        Importar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay convocatorias.</p>
        )}
      </div>
    </div>
  );
}
