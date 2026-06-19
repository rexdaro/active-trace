import { useEffect, useState } from 'react';
import api, { getCurrentUser, type User } from '../services/api';

interface Aviso {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: string;
  materia_id: string | null;
  cohorte_id: string | null;
  rol_destino: string | null;
  severidad: string;
  inicio_en: string;
  fin_en: string;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  created_at: string;
  updated_at: string;
}

interface AvisoForm {
  titulo: string;
  cuerpo: string;
  alcance: string;
  severidad: string;
  inicio_en: string;
  fin_en: string;
  activo: boolean;
  requiere_ack: boolean;
}

const alcances = ['Global', 'PorMateria', 'PorCohorte', 'PorRol'];
const severidades = ['Info', 'Advertencia', 'Crítico'];

function toDatetimeLocal(iso: string) {
  if (!iso) return '';
  return iso.slice(0, 16);
}

function toISOString(local: string) {
  if (!local) return '';
  return new Date(local).toISOString();
}

const emptyForm: AvisoForm = {
  titulo: '',
  cuerpo: '',
  alcance: 'Global',
  severidad: 'Info',
  inicio_en: '',
  fin_en: '',
  activo: true,
  requiere_ack: false,
};

export default function Avisos() {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Aviso | null>(null);
  const [form, setForm] = useState<AvisoForm>(emptyForm);
  const [user, setUser] = useState<User | null>(null);

  const canManage = user?.roles?.some((r) => r === 'COORDINADOR' || r === 'ADMIN');

  useEffect(() => {
    getCurrentUser()
      .then((u) => {
        setUser(u);
        const canManage = u?.roles?.some((r) => r === 'COORDINADOR' || r === 'ADMIN');
        const url = canManage ? '/api/v1/avisos' : '/api/v1/avisos/mis-avisos';
        return api.get(url);
      })
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
      cuerpo: a.cuerpo,
      alcance: a.alcance,
      severidad: a.severidad,
      inicio_en: toDatetimeLocal(a.inicio_en),
      fin_en: toDatetimeLocal(a.fin_en),
      activo: a.activo,
      requiere_ack: a.requiere_ack,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setError(null);
    setSuccess(null);

    if (!form.titulo.trim()) return setError('El título es requerido');
    if (!form.cuerpo.trim()) return setError('El cuerpo es requerido');
    if (!form.inicio_en) return setError('La fecha de inicio es requerida');
    if (!form.fin_en) return setError('La fecha de fin es requerida');

    try {
      const payload = {
        titulo: form.titulo,
        cuerpo: form.cuerpo,
        alcance: form.alcance,
        severidad: form.severidad,
        inicio_en: toISOString(form.inicio_en),
        fin_en: toISOString(form.fin_en),
        activo: form.activo,
        requiere_ack: form.requiere_ack,
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

  async function handleDelete(id: string) {
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
        {canManage && (
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(!showForm); }}>
            {showForm ? 'Cancelar' : 'Nuevo aviso'}
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
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>{editing ? 'Editar aviso' : 'Nuevo aviso'}</h3>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              Título *
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
              Cuerpo *
            </label>
            <textarea
              value={form.cuerpo}
              onChange={(e) => setForm((f) => ({ ...f, cuerpo: e.target.value }))}
              rows={4}
              placeholder="Contenido del aviso"
            />
          </div>

          <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '1rem' }}>
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

            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
                Severidad
              </label>
              <select
                value={form.severidad}
                onChange={(e) => setForm((f) => ({ ...f, severidad: e.target.value }))}
              >
                {severidades.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
                Inicio *
              </label>
              <input
                type="datetime-local"
                value={form.inicio_en}
                onChange={(e) => setForm((f) => ({ ...f, inicio_en: e.target.value }))}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
                Fin *
              </label>
              <input
                type="datetime-local"
                value={form.fin_en}
                onChange={(e) => setForm((f) => ({ ...f, fin_en: e.target.value }))}
              />
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.activo}
                onChange={(e) => setForm((f) => ({ ...f, activo: e.target.checked }))}
              />
              Activo
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.requiere_ack}
                onChange={(e) => setForm((f) => ({ ...f, requiere_ack: e.target.checked }))}
              />
              Requiere confirmación de lectura
            </label>
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
                  <th>Severidad</th>
                  <th>Activo</th>
                  <th>Inicio</th>
                  <th>Fin</th>
                  {canManage && <th>Acciones</th>}
                </tr>
              </thead>
              <tbody>
                {avisos.map((a) => (
                  <tr key={a.id}>
                    <td>{a.titulo}</td>
                    <td>{a.alcance}</td>
                    <td>{a.severidad}</td>
                    <td>{a.activo ? '✓' : '—'}</td>
                    <td>{new Date(a.inicio_en).toLocaleDateString()}</td>
                    <td>{new Date(a.fin_en).toLocaleDateString()}</td>
                    {canManage && (
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
                    )}
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
