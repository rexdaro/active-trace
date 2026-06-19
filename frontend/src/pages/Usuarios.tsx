import { useEffect, useState } from 'react';
import api from '../services/api';

interface Usuario {
  id: string;
  nombre: string;
  email: string;
  roles: string[];
  activo: boolean;
}

interface Role {
  id: number;
  name: string;
}

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [crearOpen, setCrearOpen] = useState(false);
  const [editando, setEditando] = useState<Usuario | null>(null);
  const [mostrar, setMostrar] = useState<'activos' | 'inactivos'>('activos');

  useEffect(() => {
    loadUsuarios();
  }, [mostrar]);

  async function loadUsuarios() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/usuarios', {
        params: { estado: mostrar },
      });
      setUsuarios(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  }

  function showMsg(msg: string) {
    setSuccess(msg);
    setTimeout(() => setSuccess(null), 4000);
  }

  async function handleToggleActivo(id: string, activo: boolean) {
    const action = activo ? 'desactivar' : 'activar';
    if (!confirm(`¿Confirmás ${action} este usuario?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await api.put(`/api/v1/usuarios/${id}/toggle-activo`);
      showMsg(`Usuario ${action}do correctamente`);
      loadUsuarios();
    } catch {
      setError(`Error al ${action} usuario`);
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Usuarios</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="toggle-switch">
            <button
              className={`toggle-opt ${mostrar === 'activos' ? 'active' : ''}`}
              onClick={() => setMostrar('activos')}
            >
              Activos
            </button>
            <button
              className={`toggle-opt ${mostrar === 'inactivos' ? 'active' : ''}`}
              onClick={() => setMostrar('inactivos')}
            >
              Inactivos
            </button>
          </div>
          <button className="btn btn-primary" onClick={() => setCrearOpen(true)}>
            + Crear usuario
          </button>
        </div>
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
                      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                        <button className="btn btn-ghost" onClick={() => setEditando(u)}>
                          Editar
                        </button>
                        <button
                          className={`btn ${u.activo ? 'btn-danger' : 'btn-primary'}`}
                          onClick={() => handleToggleActivo(u.id, u.activo)}
                        >
                          {u.activo ? 'Desactivar' : 'Activar'}
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

      {crearOpen && (
        <CreateUserModal
          onClose={() => setCrearOpen(false)}
          onCreated={() => {
            setCrearOpen(false);
            showMsg('Usuario creado correctamente');
            loadUsuarios();
          }}
        />
      )}

      {editando && (
        <EditUserModal
          user={editando}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null);
            showMsg('Usuario actualizado correctamente');
            loadUsuarios();
          }}
        />
      )}
    </div>
  );
}

interface UserRole {
  id: number;
  name: string;
}

function EditUserModal({ user, onClose, onSaved }: { user: Usuario; onClose: () => void; onSaved: () => void }) {
  const [detalleRoles, setDetalleRoles] = useState<UserRole[]>([]);
  const [allRoles, setAllRoles] = useState<UserRole[]>([]);
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [dni, setDni] = useState('');
  const [cuil, setCuil] = useState('');
  const [password, setPassword] = useState('');
  const [rolAgregar, setRolAgregar] = useState<number | ''>('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [roleMsg, setRoleMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get(`/api/v1/usuarios/${user.id}`),
      api.get('/api/v1/usuarios/roles'),
    ])
      .then(([detailRes, rolesRes]) => {
        const d = detailRes.data;
        setNombre(d.nombre ?? '');
        setEmail(d.email);
        setDni(d.dni ?? '');
        setCuil(d.cuil ?? '');
        setDetalleRoles(d.roles ?? []);
        setAllRoles(rolesRes.data);
      })
      .catch(() => setError('Error al cargar datos del usuario'))
      .finally(() => setLoading(false));
  }, [user.id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) { setError('El email es obligatorio'); return; }

    setSaving(true);
    setError(null);
    try {
      const body: Record<string, any> = {
        nombre: nombre || null,
        email,
        dni: dni || null,
        cuil: cuil || null,
      };
      if (password) body.password = password;

      await api.put(`/api/v1/usuarios/${user.id}`, body);
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al actualizar usuario');
    } finally {
      setSaving(false);
    }
  }

  async function handleAgregarRol() {
    if (rolAgregar === '') return;
    const rol = allRoles.find((r) => r.id === rolAgregar);
    if (!rol) return;
    setRoleMsg(null);
    try {
      await api.post(`/api/v1/usuarios/${user.id}/roles`, { rol: rol.name });
      setDetalleRoles((prev) => [...prev, rol]);
      setRolAgregar('');
      setRoleMsg(`Rol "${rol.name}" asignado`);
    } catch {
      setRoleMsg(`Error al asignar rol "${rol.name}"`);
    }
    setTimeout(() => setRoleMsg(null), 3000);
  }

  async function handleRemoverRol(role: UserRole) {
    if (!confirm(`¿Sacar el rol "${role.name}"?`)) return;
    setRoleMsg(null);
    try {
      await api.delete(`/api/v1/usuarios/${user.id}/roles/${role.id}`);
      setDetalleRoles((prev) => prev.filter((r) => r.id !== role.id));
      setRoleMsg(`Rol "${role.name}" removido`);
    } catch {
      setRoleMsg(`Error al remover rol "${role.name}"`);
    }
    setTimeout(() => setRoleMsg(null), 3000);
  }

  const rolesDisponibles = allRoles.filter(
    (r) => !detalleRoles.some((dr) => dr.id === r.id)
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Editar usuario</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {loading ? (
          <div className="modal-body">
            <div className="loading">Cargando datos...</div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}
            <div className="modal-body">
              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Nombre</label>
                  <input
                    type="text"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    placeholder="Nombre y apellido"
                  />
                </div>
                <div className="form-group">
                  <label>Nueva contraseña</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Dejar vacío para no cambiar"
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>DNI</label>
                  <input
                    type="text"
                    value={dni}
                    onChange={(e) => setDni(e.target.value)}
                    placeholder="12345678"
                  />
                </div>
                <div className="form-group">
                  <label>CUIT/CUIL</label>
                  <input
                    type="text"
                    value={cuil}
                    onChange={(e) => setCuil(e.target.value)}
                    placeholder="20-12345678-9"
                  />
                </div>
              </div>

              {/* Roles section */}
              <div style={{ marginTop: '0.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Roles
                </label>
                {roleMsg && (
                  <div style={{ fontSize: '0.8rem', color: roleMsg.includes('Error') ? 'var(--danger)' : 'var(--success)', marginBottom: '0.5rem' }}>
                    {roleMsg}
                  </div>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
                  {detalleRoles.length === 0 && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sin roles asignados</span>
                  )}
                  {detalleRoles.map((r) => (
                    <span
                      key={r.id}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        padding: '0.2rem 0.6rem',
                        background: '#eef2ff',
                        color: 'var(--primary)',
                        borderRadius: '999px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                      }}
                    >
                      {r.name}
                      <button
                        type="button"
                        onClick={() => handleRemoverRol(r)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: '#94a3b8',
                          fontSize: '0.85rem',
                          padding: 0,
                          lineHeight: 1,
                        }}
                        title="Sacar rol"
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
                {rolesDisponibles.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <select
                      value={rolAgregar}
                      onChange={(e) => setRolAgregar(e.target.value ? Number(e.target.value) : '')}
                      style={{ flex: 1 }}
                    >
                      <option value="">— Agregar rol —</option>
                      {rolesDisponibles.map((r) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </select>
                    <button type="button" className="btn btn-primary" onClick={handleAgregarRol} disabled={rolAgregar === ''}>
                      +
                    </button>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Guardando...' : 'Guardar cambios'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nombre, setNombre] = useState('');
  const [dni, setDni] = useState('');
  const [cuil, setCuil] = useState('');
  const [roleId, setRoleId] = useState<number | ''>('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/api/v1/usuarios/roles')
      .then((res) => setRoles(res.data))
      .catch(() => setError('Error al cargar roles'));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) {
      setError('Email y contraseña son obligatorios');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.post('/api/v1/usuarios', {
        email,
        password,
        nombre: nombre || undefined,
        dni: dni || undefined,
        cuil: cuil || undefined,
        role_id: roleId !== '' ? roleId : undefined,
      });
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear usuario');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Crear usuario</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="modal-body">
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="usuario@ejemplo.com"
                required
              />
            </div>
            <div className="form-group">
              <label>Contraseña *</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Nombre</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Nombre y apellido"
                />
              </div>
              <div className="form-group">
                <label>Rol</label>
                <select value={roleId} onChange={(e) => setRoleId(e.target.value ? Number(e.target.value) : '')}>
                  <option value="">— Sin rol (ALUMNO por defecto) —</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>DNI</label>
                <input
                  type="text"
                  value={dni}
                  onChange={(e) => setDni(e.target.value)}
                  placeholder="12345678"
                />
              </div>
              <div className="form-group">
                <label>CUIT/CUIL</label>
                <input
                  type="text"
                  value={cuil}
                  onChange={(e) => setCuil(e.target.value)}
                  placeholder="20-12345678-9"
                />
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Creando...' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
