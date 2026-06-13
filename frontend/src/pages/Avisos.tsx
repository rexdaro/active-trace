import { useEffect, useState } from 'react';
import api from '../services/api';

interface Aviso {
  id: number;
  titulo: string;
  contenido: string;
  alcance: string;
  filtro_id: number | null;
  created_at: string;
  confirmacion_lectura: number;
}

interface AvisoForm {
  titulo: string;
  contenido: string;
  alcance: string;
  filtro_id: string;
}

const alcances = ['Global', 'PorMateria', 'PorCohorte', 'PorRol'];

const emptyForm: AvisoForm = {
  titulo: '',
  contenido: '',
  alcance: 'Global',
  filtro_id: '',
};

export default function Avisos() {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Aviso | null>(null);
  const [form, setForm] = useState<AvisoForm>(emptyForm);

  useEffect(() => {
    api
      .get('/api/v1/avisos')
      .then((res) => setAvisos(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar avisos'))
      .finally(() => setLoading(false));
  }, []);

  function resetForm() {
    setForm(emptyForm);
    setEditing(null);
    setShowForm(false);
  }

  function startEdit(a: Aviso) {
    setEditing(a);
    setForm({
      titulo: a.titulo,
      contenido: a.contenido,
      alcance: a.alcance,
      filtro_id: a.filtro_id?.toString() || '',
    });
    setShowForm(true);
  }

  async function handleSave() {
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        titulo: form.titulo,
        contenido: form.contenido,
        alcance: form.alcance,
        filtro_id: form.filtro_id ? Number(form.filtro_id) : null,
      };

      if (editing) {
        await api.put(`/api/v1/avisos/${editing.id}`, payload);
        setSuccess('Aviso actualizado');
      } else {
        await api.post('/api/v1/avisos', payload);
        setSuccess('Aviso creado');
      }

      const res = await api.get('/api/v1/avisos');
      setAvisos(Array.isArray(res.data) ? res.data : []);
      resetForm();
    } catch {
      setError('Error al guardar aviso');
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('¿Eliminar este aviso?')) return;
    try {
      await api.delete(`/api/v1/avisos/${id}`);
      setAvisos((prev) => prev.filter((a) => a.id !== id));
      setSuccess('Aviso eliminado');
    } catch {
      setError('Error al eliminar aviso');
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Avisos</h1>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(!showForm); }}>
          {showForm ? 'Cancelar' : 'Nuevo aviso'}
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
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>{editing ? 'Editar aviso' : 'Nuevo aviso'}</h3>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              Título
            </label>
            <input
              type="text"
              value={form.titulo}
              onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
              placeholder="Título del aviso"
            />
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              Contenido
            </label>
            <textarea
              value={form.contenido}
              onChange={(e) => setForm((f) => ({ ...f, contenido: e.target.value }))}
              rows={4}
              placeholder="Contenido del aviso"
            />
          </div>

          <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
                Alcance
              </label>
              <select
                value={form.alcance}
                onChange={(e) => setForm((f) => ({ ...f, alcance: e.target.value }))}
              >
                {alcances.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            {form.alcance !== 'Global' && (
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
                  ID de {form.alcance === 'PorMateria' ? 'materia' : form.alcance === 'PorCohorte' ? 'cohorte' : 'rol'}
                </label>
                <input
                  type="number"
                  value={form.filtro_id}
                  onChange={(e) => setForm((f) => ({ ...f, filtro_id: e.target.value }))}
                />
              </div>
            )}
          </div>

          <button className="btn btn-primary" onClick={handleSave}>
            {editing ? 'Guardar cambios' : 'Crear aviso'}
          </button>
        </div>
      )}

      <div className="card">
        {avisos.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Alcance</th>
                  <th>Lecturas</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {avisos.map((a) => (
                  <tr key={a.id}>
                    <td>{a.titulo}</td>
                    <td>{a.alcance}{a.filtro_id ? ` (${a.filtro_id})` : ''}</td>
                    <td>{a.confirmacion_lectura ?? 0}</td>
                    <td>{new Date(a.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => startEdit(a)}
                        >
                          Editar
                        </button>
                        <button
                          className="btn btn-danger"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => handleDelete(a.id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay avisos.</p>
        )}
      </div>
    </div>
  );
}
