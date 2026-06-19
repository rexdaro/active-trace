import { useEffect, useState } from 'react';
import api, { getCurrentUser, type User } from '../services/api';

interface Convocatoria {
  id: string;
  materia_id: string;
  materia_nombre: string;
  cohorte_id: string;
  tipo: string;
  instancia: string;
  cupos_por_dia: number;
  total_alumnos: number;
  reservas_activas: number;
  created_at: string;
}

interface Materia {
  id: string;
  name: string;
  code: string;
}

interface Cohorte {
  id: string;
  name: string;
}

type Metricas = Record<string, { convocados: number; reservas: number; libres: number }>;

export default function Coloquios() {
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [cohortes, setCohortes] = useState<Cohorte[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const puedeCrear = user?.roles?.some((r) => r === 'COORDINADOR' || r === 'ADMIN');
  const puedeImportar = user?.roles?.some((r) => r === 'COORDINADOR' || r === 'ADMIN' || r === 'PROFESOR');

  // Form state (matches EvaluacionCreate schema)
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [tipo, setTipo] = useState('Coloquio');
  const [instancia, setInstancia] = useState('');
  const [cuposPorDia, setCuposPorDia] = useState('10');

  const [metricas, setMetricas] = useState<Metricas>({});
  const [loadingMetricas, setLoadingMetricas] = useState<Record<string, boolean>>({});

  useEffect(() => {
    getCurrentUser()
      .then((u) => {
        setUser(u);
        return Promise.all([
          api.get('/api/v1/coloquios'),
          api.get('/api/materias'),
          api.get('/api/cohortes'),
        ]);
      })
      .then(([colRes, matRes, cohRes]) => {
        const colData = colRes.data;
        setConvocatorias(Array.isArray(colData) ? colData : (colData?.items ?? []));
        setMaterias(Array.isArray(matRes.data) ? matRes.data : []);
        setCohortes(Array.isArray(cohRes.data) ? cohRes.data : []);
      }).catch(() => setError('Error al cargar datos'))
      .finally(() => setLoading(false));
  }, []);

  function resetForm() {
    setMateriaId('');
    setCohorteId('');
    setTipo('Coloquio');
    setInstancia('');
    setCuposPorDia('10');
  }

  async function handleCreate() {
    if (!materiaId || !cohorteId || !instancia) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/coloquios', {
        materia_id: materiaId,
        cohorte_id: cohorteId,
        tipo,
        instancia,
        cupos_por_dia: Number(cuposPorDia) || 10,
      });
      setSuccess('Convocatoria creada');
      resetForm();
      setShowForm(false);
      const res = await api.get('/api/v1/coloquios');
      const data = res.data;
      setConvocatorias(Array.isArray(data) ? data : (data?.items ?? []));
    } catch {
      setError('Error al crear convocatoria');
    }
  }

  async function handleImportar(id: string) {
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/api/v1/coloquios/${id}/importar`);
      setSuccess('Alumnos importados');
      const res = await api.get('/api/v1/coloquios');
      const data = res.data;
      setConvocatorias(Array.isArray(data) ? data : (data?.items ?? []));
    } catch {
      setError('Error al importar alumnos');
    }
  }

  async function handleMetricas(id: string) {
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
        {puedeCrear && (
          <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); resetForm(); }}>
            {showForm ? 'Cancelar' : 'Nueva convocatoria'}
          </button>
        )}
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
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Materia</label>
            <select value={materiaId} onChange={(e) => setMateriaId(e.target.value)}>
              <option value="">Seleccionar materia...</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.name} ({m.code})</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Cohorte</label>
            <select value={cohorteId} onChange={(e) => setCohorteId(e.target.value)}>
              <option value="">Seleccionar cohorte...</option>
              {cohortes.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Tipo</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="Coloquio">Coloquio</option>
              <option value="Final">Final</option>
              <option value="Parcial">Parcial</option>
              <option value="Recuperatorio">Recuperatorio</option>
            </select>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Instancia</label>
            <input type="text" value={instancia} onChange={(e) => setInstancia(e.target.value)} placeholder="ej: 2025-Julio" />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Cupos por día</label>
            <input type="number" min={1} value={cuposPorDia} onChange={(e) => setCuposPorDia(e.target.value)} />
          </div>

          <button className="btn btn-primary" onClick={handleCreate} disabled={!materiaId || !cohorteId || !instancia}>
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
                  <th>Tipo</th>
                  <th>Instancia</th>
                  <th>Cupos/día</th>
                  <th>Alumnos</th>
                  <th>Reservas</th>
                  <th>Métricas</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {convocatorias.map((c) => (
                  <tr key={c.id}>
                    <td>{c.materia_nombre || c.materia_id.slice(0, 8) + '…'}</td>
                    <td>{c.tipo}</td>
                    <td>{c.instancia}</td>
                    <td>{c.cupos_por_dia}</td>
                    <td>{c.total_alumnos}</td>
                    <td>{c.reservas_activas}</td>
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
                      {puedeImportar && (
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => handleImportar(c.id)}
                        >
                          Importar
                        </button>
                      )}
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
