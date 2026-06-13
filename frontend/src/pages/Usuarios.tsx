import { useEffect, useState } from 'react';
import api from '../services/api';

interface Usuario {
  id: number;
  nombre: string;
  email: string;
  roles: string[];
  activo: boolean;
}

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadUsuarios();
  }, []);

  async function loadUsuarios() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/usuarios');
      setUsuarios(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleActivo(id: number, activo: boolean) {
    const action = activo ? 'desactivar' : 'activar';
    if (!confirm(`¿Confirmás ${action} este usuario?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await api.put(`/api/v1/usuarios/${id}/toggle-activo`);
      setSuccess(`Usuario ${action}do correctamente`);
      loadUsuarios();
    } catch {
      setError(`Error al ${action} usuario`);
    }
  }

  async function handleAsignarRol(id: number) {
    const rol = prompt('Ingresá el rol a asignar:');
    if (!rol) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/api/v1/usuarios/${id}/roles`, { rol });
      setSuccess('Rol asignado correctamente');
      loadUsuarios();
    } catch {
      setError('Error al asignar rol');
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Usuarios</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="card">
        {usuarios.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Email</th>
                  <th>Roles</th>
                  <th>Activo</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u) => (
                  <tr key={u.id}>
                    <td>{u.nombre}</td>
                    <td>{u.email}</td>
                    <td>{u.roles.join(', ')}</td>
                    <td>
                      <span style={{
                        display: 'inline-block',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: u.activo ? 'var(--success)' : 'var(--danger)',
                        marginRight: '0.5rem',
                      }} />
                      {u.activo ? 'Sí' : 'No'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          className={`btn ${u.activo ? 'btn-danger' : 'btn-primary'}`}
                          onClick={() => handleToggleActivo(u.id, u.activo)}
                        >
                          {u.activo ? 'Desactivar' : 'Activar'}
                        </button>
                        <button className="btn btn-ghost" onClick={() => handleAsignarRol(u.id)}>
                          Asignar rol
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay usuarios cargados.</p>
        )}
      </div>
    </div>
  );
}
