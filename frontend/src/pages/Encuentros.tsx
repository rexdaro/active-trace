import { useEffect, useState } from 'react';
import api from '../services/api';

interface Encuentro {
  id: number;
  materia: string;
  titulo: string;
  recurrente: boolean;
  cant_semanas: number | null;
  fecha: string;
}

export default function Encuentros() {
  const [encuentros, setEncuentros] = useState<Encuentro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [titulo, setTitulo] = useState('');
  const [materiaId, setMateriaId] = useState('');
  const [fecha, setFecha] = useState('');
  const [recurrente, setRecurrente] = useState(false);
  const [cantSemanas, setCantSemanas] = useState('');

  useEffect(() => {
    api
      .get('/api/v1/encuentros')
      .then((res) => setEncuentros(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar encuentros'))
      .finally(() => setLoading(false));
  }, []);

  function resetForm() {
    setTitulo('');
    setMateriaId('');
    setFecha('');
    setRecurrente(false);
    setCantSemanas('');
  }

  async function handleCreate() {
    if (!titulo || !materiaId || !fecha) return;
    setError(null);
    setSuccess(null);
    try {
      const payload: Record<string, unknown> = {
        titulo,
        materia_id: Number(materiaId),
        fecha,
      };
      if (recurrente) {
        payload.recurrente = true;
        payload.cant_semanas = Number(cantSemanas) || 1;
      }

      await api.post('/api/v1/encuentros', payload);
      setSuccess('Encuentro creado');
      resetForm();
      setShowForm(false);

      const res = await api.get('/api/v1/encuentros');
      setEncuentros(Array.isArray(res.data) ? res.data : []);
    } catch {
      setError('Error al crear encuentro');
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Encuentros</h1>
        <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); resetForm(); }}>
          {showForm ? 'Cancelar' : 'Nuevo encuentro'}
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
          <h3 style={{ marginBottom: '1rem' }}>Crear encuentro</h3>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Título</label>
            <input type="text" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título del encuentro" />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Materia ID</label>
            <input type="number" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} placeholder="ID de materia" />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Fecha</label>
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          </div>

          <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input type="checkbox" id="recurrente" checked={recurrente} onChange={(e) => setRecurrente(e.target.checked)} />
            <label htmlFor="recurrente" style={{ fontSize: '0.9rem' }}>Recurrente</label>
          </div>

          {recurrente && (
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Semanas</label>
              <input type="number" min={1} value={cantSemanas} onChange={(e) => setCantSemanas(e.target.value)} placeholder="Cantidad de semanas" />
            </div>
          )}

          <button className="btn btn-primary" onClick={handleCreate} disabled={!titulo || !materiaId || !fecha}>
            Crear
          </button>
        </div>
      )}

      <div className="card">
        {encuentros.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Materia</th>
                  <th>Título</th>
                  <th>Tipo</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {encuentros.map((e) => (
                  <tr key={e.id}>
                    <td>{e.materia}</td>
                    <td>{e.titulo}</td>
                    <td>{e.recurrente ? `Recurrente (${e.cant_semanas} sem)` : 'Único'}</td>
                    <td>{new Date(e.fecha).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay encuentros.</p>
        )}
      </div>
    </div>
  );
}
