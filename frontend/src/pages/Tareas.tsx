import { useEffect, useState, useMemo } from 'react';
import api from '../services/api';

interface Tarea {
  id: number;
  descripcion: string;
  asignado_a: string;
  estado: string;
  created_at: string;
}

interface Comentario {
  id: number;
  autor: string;
  texto: string;
  autor_id?: string;
  created_at: string;
}

const estados = ['Pendiente', 'En progreso', 'Resuelta', 'Cancelada'];

interface UserOption {
  id: string;
  email: string;
  nombre: string;
}

type ModalType = 'estado' | 'comentar' | null;

export default function Tareas() {
  const [tareas, setTareas] = useState<Tarea[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [verTodas, setVerTodas] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [nuevaDesc, setNuevaDesc] = useState('');
  const [nuevoUserId, setNuevoUserId] = useState('');

  // Comments loaded per tarea (lazy)
  const [comentariosMap, setComentariosMap] = useState<Record<string, Comentario[]>>({});
  const [loadingComentarios, setLoadingComentarios] = useState<Record<string, boolean>>({});

  // Modal state
  const [modal, setModal] = useState<ModalType>(null);
  const [modalTareaId, setModalTareaId] = useState<number | null>(null);
  const [modalEstado, setModalEstado] = useState('Pendiente');
  const [modalTexto, setModalTexto] = useState('');

  // Build user map: UUID → "email — nombre"
  const userMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const u of users) {
      map[u.id] = `${u.email} — ${u.nombre}`;
    }
    return map;
  }, [users]);

  function cargar() {
    setLoading(true);
    const params: Record<string, string> = {};
    if (filtroEstado) params.estado = filtroEstado;
    const url = verTodas ? '/api/v1/tareas/admin' : '/api/v1/tareas';

    api
      .get(url, { params })
      .then((res) => setTareas(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar tareas'))
      .finally(() => setLoading(false));
  }

  useEffect(() => { cargar(); }, [filtroEstado, verTodas]);

  // Load users for the asignar dropdown and name resolution
  useEffect(() => {
    api.get('/api/v1/usuarios')
      .then((res) => setUsers(Array.isArray(res.data) ? res.data : []))
      .catch(() => {});
  }, []);

  async function loadComentarios(tareaId: number | string) {
    const key = String(tareaId);
    if (comentariosMap[key]) return; // already loaded
    setLoadingComentarios((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await api.get(`/api/v1/tareas/${key}/comentarios`);
      setComentariosMap((prev) => ({ ...prev, [key]: Array.isArray(res.data) ? res.data : [] }));
    } catch {
      // ignore
    } finally {
      setLoadingComentarios((prev) => ({ ...prev, [key]: false }));
    }
  }

  async function handleAsignar() {
    if (!nuevaDesc || !nuevoUserId) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/tareas', {
        descripcion: nuevaDesc,
        asignado_a: nuevoUserId,
      });
      setSuccess('Tarea asignada');
      setNuevaDesc('');
      setNuevoUserId('');
      setShowForm(false);
      cargar();
    } catch {
      setError('Error al asignar tarea');
    }
  }

  function openModal(type: ModalType, tareaId: number, estadoActual?: string) {
    setModal(type);
    setModalTareaId(tareaId);
    setModalEstado(estadoActual || 'Pendiente');
    setModalTexto('');
  }

  function closeModal() {
    setModal(null);
    setModalTareaId(null);
  }

  async function handleCambiarEstado() {
    if (modalTareaId === null) return;
    try {
      await api.put(`/api/v1/tareas/${modalTareaId}/estado`, { estado: modalEstado });
      setSuccess('Estado actualizado');
      closeModal();
      cargar();
    } catch {
      setError('Error al actualizar estado');
    }
  }

  async function handleComentar() {
    if (modalTareaId === null || !modalTexto.trim()) return;
    try {
      await api.post(`/api/v1/tareas/${modalTareaId}/comentarios`, { texto: modalTexto });
      setSuccess('Comentario agregado');
      closeModal();
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
              Asignar a
            </label>
            <select value={nuevoUserId} onChange={(e) => setNuevoUserId(e.target.value)} style={{ maxWidth: '400px' }}>
              <option value="">Seleccionar usuario...</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.email} — {u.nombre}</option>
              ))}
            </select>
          </div>
          <button className="btn btn-primary" onClick={handleAsignar} disabled={!nuevaDesc || !nuevoUserId}>
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
                    <td>{userMap[t.asignado_a] || t.asignado_a.slice(0, 8) + '…'}</td>
                    <td>{t.estado}</td>
                    <td>{new Date(t.created_at).toLocaleDateString()}</td>
                    <td>
                      <details onToggle={(e) => { if ((e.target as HTMLDetailsElement).open) loadComentarios(t.id); }}>
                        <summary style={{ cursor: 'pointer', fontSize: '0.85rem', userSelect: 'none' }}>
                          {loadingComentarios[String(t.id)] ? 'Cargando...' : (comentariosMap[String(t.id)] ? `${comentariosMap[String(t.id)].length} comentarios` : 'Ver comentarios')}
                        </summary>
                        {comentariosMap[String(t.id)]?.length > 0 ? (
                          comentariosMap[String(t.id)].map((c) => (
                            <div key={c.id} style={{ fontSize: '0.8rem', marginTop: '0.25rem', padding: '0.25rem 0', borderBottom: '1px solid var(--border)' }}>
                              <strong>{c.autor}</strong>: {c.texto}
                              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{new Date(c.created_at).toLocaleDateString()}</div>
                            </div>
                          ))
                        ) : (
                          !loadingComentarios[String(t.id)] && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', padding: '0.25rem 0' }}>Sin comentarios</div>
                        )}
                      </details>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => openModal('estado', t.id, t.estado)}
                        >
                          Estado
                        </button>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                          onClick={() => openModal('comentar', t.id)}
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

      {/* ─── Modal: cambiar estado ─── */}
      {modal === 'estado' && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '1rem' }}>Cambiar estado</h3>
            <select
              value={modalEstado}
              onChange={(e) => setModalEstado(e.target.value)}
              style={{ width: '100%', marginBottom: '1rem' }}
            >
              {estados.map((e) => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={closeModal}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleCambiarEstado}>Guardar</button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Modal: agregar comentario ─── */}
      {modal === 'comentar' && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '1rem' }}>Agregar comentario</h3>
            <textarea
              value={modalTexto}
              onChange={(e) => setModalTexto(e.target.value)}
              rows={4}
              placeholder="Escribí tu comentario..."
              style={{ width: '100%', marginBottom: '1rem' }}
            />
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={closeModal}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleComentar} disabled={!modalTexto.trim()}>
                Enviar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
