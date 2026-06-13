import { useEffect, useState } from 'react';
import api from '../services/api';

interface Tarea {
  id: number;
  descripcion: string;
  asignado_a: string;
  estado: string;
  created_at: string;
  comentarios: Comentario[];
}

interface Comentario {
  id: number;
  autor: string;
  contenido: string;
  created_at: string;
}

const estados = ['Pendiente', 'En progreso', 'Resuelta', 'Cancelada'];

export default function Tareas() {
  const [tareas, setTareas] = useState<Tarea[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [verTodas, setVerTodas] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [nuevaDesc, setNuevaDesc] = useState('');
  const [nuevoUser, setNuevoUser] = useState('');

  function cargar() {
    setLoading(true);
    const params: Record<string, string> = {};
    if (filtroEstado) params.estado = filtroEstado;
    if (verTodas) params.todas = 'true';

    api
      .get('/api/v1/tareas', { params })
      .then((res) => setTareas(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar tareas'))
      .finally(() => setLoading(false));
  }

  useEffect(() => { cargar(); }, [filtroEstado, verTodas]);

  async function handleAsignar() {
    if (!nuevaDesc || !nuevoUser) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/tareas', {
        descripcion: nuevaDesc,
        asignado_a: nuevoUser,
      });
      setSuccess('Tarea asignada');
      setNuevaDesc('');
      setNuevoUser('');
      setShowForm(false);
      cargar();
    } catch {
      setError('Error al asignar tarea');
    }
  }

  async function handleCambiarEstado(id: number) {
    const estado = prompt('Nuevo estado: Pendiente / En progreso / Resuelta / Cancelada');
    if (!estado || !estados.includes(estado)) return;
    try {
      await api.put(`/api/v1/tareas/${id}/estado`, { estado });
      setSuccess('Estado actualizado');
      cargar();
    } catch {
      setError('Error al actualizar estado');
    }
  }

  async function handleComentar(id: number) {
    const contenido = prompt('Escribí tu comentario:');
    if (!contenido) return;
    try {
      await api.post(`/api/v1/tareas/${id}/comentarios`, { contenido });
      setSuccess('Comentario agregado');
      cargar();
    } catch {
      setError('Error al agregar comentario');
    }
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Tareas</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancelar' : 'Asignar tarea'}
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

      <div className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
            Filtrar por estado
          </label>
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} style={{ minWidth: '160px' }}>
            <option value="">Todos</option>
            {estados.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={verTodas} onChange={(e) => setVerTodas(e.target.checked)} />
          <span style={{ fontSize: '0.9rem' }}>Ver todas (admin)</span>
        </label>
      </div>

      {showForm && (
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Asignar tarea</h3>
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              Descripción
            </label>
            <textarea
              value={nuevaDesc}
              onChange={(e) => setNuevaDesc(e.target.value)}
              rows={3}
              placeholder="Descripción de la tarea"
            />
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              Asignar a (email)
            </label>
            <input
              type="text"
              value={nuevoUser}
              onChange={(e) => setNuevoUser(e.target.value)}
              placeholder="email del usuario"
              style={{ maxWidth: '300px' }}
            />
          </div>
          <button className="btn btn-primary" onClick={handleAsignar} disabled={!nuevaDesc || !nuevoUser}>
            Asignar
          </button>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading">Cargando...</div>
        ) : tareas.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Descripción</th>
                  <th>Asignado a</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Comentarios</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {tareas.map((t) => (
                  <tr key={t.id}>
                    <td>{t.descripcion}</td>
                    <td>{t.asignado_a}</td>
                    <td>{t.estado}</td>
                    <td>{new Date(t.created_at).toLocaleDateString()}</td>
                    <td>
                      {t.comentarios?.length > 0 ? (
                        <details>
                          <summary style={{ cursor: 'pointer', fontSize: '0.85rem' }}>
                            {t.comentarios.length} comentarios
                          </summary>
                          {t.comentarios.map((c) => (
                            <div key={c.id} style={{ fontSize: '0.8rem', marginTop: '0.25rem', padding: '0.25rem 0', borderBottom: '1px solid var(--border)' }}>
                              <strong>{c.autor}</strong>: {c.contenido}
                              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{new Date(c.created_at).toLocaleDateString()}</div>
                            </div>
                          ))}
                        </details>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>—</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => handleCambiarEstado(t.id)}
                        >
                          Estado
                        </button>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => handleComentar(t.id)}
                        >
                          Comentar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay tareas.</p>
        )}
      </div>
    </div>
  );
}
