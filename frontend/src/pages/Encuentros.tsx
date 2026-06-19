import { useEffect, useState, useMemo } from 'react';
import api from '../services/api';

interface Encuentro {
  id: string;
  materia_id: string;
  titulo: string;
  fecha: string;
  hora: string;
  estado: string;
  meet_url: string | null;
}

interface Materia {
  id: string;
  name: string;
  code: string;
}

export default function Encuentros() {
  const [encuentros, setEncuentros] = useState<Encuentro[]>([]);
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [titulo, setTitulo] = useState('');
  const [materiaId, setMateriaId] = useState('');
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [meetUrl, setMeetUrl] = useState('');

  // Build materia map
  const materiaMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const m of materias) {
      map[m.id] = m.name;
    }
    return map;
  }, [materias]);

  useEffect(() => {
    api.get('/api/v1/encuentros')
      .then((res) => setEncuentros(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar encuentros'))
      .finally(() => setLoading(false));

    api.get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => {});
  }, []);

  function resetForm() {
    setTitulo('');
    setMateriaId('');
    setFecha('');
    setHora('');
    setMeetUrl('');
  }

  async function handleCreate() {
    if (!titulo || !materiaId || !fecha || !hora) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/encuentros/unico', {
        titulo,
        materia_id: materiaId,
        fecha,
        hora,
        meet_url: meetUrl || null,
      });
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
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Materia</label>
            <select value={materiaId} onChange={(e) => setMateriaId(e.target.value)}>
              <option value="">Seleccionar materia...</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.name} ({m.code})</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Título</label>
            <input type="text" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título del encuentro" />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Fecha</label>
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Hora</label>
            <input type="time" value={hora} onChange={(e) => setHora(e.target.value)} />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>Meet URL (opcional)</label>
            <input type="url" value={meetUrl} onChange={(e) => setMeetUrl(e.target.value)} placeholder="https://meet.google.com/..." />
          </div>

          <button className="btn btn-primary" onClick={handleCreate} disabled={!titulo || !materiaId || !fecha || !hora}>
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
                  <th>Fecha</th>
                  <th>Hora</th>
                  <th>Estado</th>
                  <th>Meet</th>
                </tr>
              </thead>
              <tbody>
                {encuentros.map((e) => (
                  <tr key={e.id}>
                    <td>{materiaMap[e.materia_id] || e.materia_id.slice(0, 8) + '…'}</td>
                    <td>{e.titulo}</td>
                    <td>{new Date(e.fecha + 'T00:00:00').toLocaleDateString()}</td>
                    <td>{e.hora}</td>
                    <td>{e.estado}</td>
                    <td>{e.meet_url ? <a href={e.meet_url} target="_blank" rel="noopener noreferrer">Abrir</a> : '—'}</td>
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
