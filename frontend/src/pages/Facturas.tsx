import { useEffect, useState } from 'react';
import api from '../services/api';

interface Factura {
  id: string;
  usuario_id: string;
  periodo: string;
  detalle: string;
  fecha: string;
  monto: number;
  estado: string;
  abonada_at: string | null;
  created_at: string;
}

interface UserOption {
  id: string;
  email: string;
  nombre: string;
}

export default function Facturas() {
  const [facturas, setFacturas] = useState<Factura[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [usuarioId, setUsuarioId] = useState('');
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [fecha, setFecha] = useState(() => new Date().toISOString().split('T')[0]);
  const [monto, setMonto] = useState('');
  const [detalle, setDetalle] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadFacturas();
    api.get('/api/v1/usuarios')
      .then((res) => setUsers(Array.isArray(res.data) ? res.data : []))
      .catch(() => {});
  }, []);

  async function loadFacturas() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/facturas');
      setFacturas(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar facturas');
    } finally {
      setLoading(false);
    }
  }

  async function handleCargar(e: React.FormEvent) {
    e.preventDefault();
    if (!usuarioId || !detalle || !periodo || !fecha || !monto) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/facturas', {
        usuario_id: usuarioId,
        periodo,
        detalle,
        fecha,
        monto: Number(monto),
      });
      setSuccess('Factura cargada correctamente');
      setDetalle('');
      setUsuarioId('');
      setMonto('');
      loadFacturas();
    } catch {
      setError('Error al cargar factura');
    } finally {
      setSaving(false);
    }
  }

  async function handleAbonar(id: string) {
    if (!confirm('¿Confirmás marcar esta factura como abonada?')) return;
    setError(null);
    setSuccess(null);
    try {
      await api.put(`/api/v1/facturas/${id}/abonar`);
      setSuccess('Factura abonada correctamente');
      loadFacturas();
    } catch {
      setError('Error al abonar factura');
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Facturas</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Cargar factura</h2>
        <form onSubmit={handleCargar} style={{ maxWidth: '500px' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Docente</label>
            <select value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} required>
              <option value="">Seleccionar docente...</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.email} — {u.nombre}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Período</label>
            <input type="month" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required style={{ maxWidth: '200px' }} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Fecha de la factura</label>
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required style={{ maxWidth: '200px' }} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Monto</label>
            <input type="number" step="0.01" min="0" value={monto} onChange={(e) => setMonto(e.target.value)} placeholder="0.00" required style={{ maxWidth: '200px' }} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Detalle</label>
            <textarea
              value={detalle}
              onChange={(e) => setDetalle(e.target.value)}
              placeholder="Detalle de la factura"
              rows={3}
              required
            />
          </div>

          <button className="btn btn-primary" type="submit" disabled={saving || !usuarioId || !detalle || !periodo || !fecha || !monto}>
            {saving ? 'Guardando...' : 'Cargar factura'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Listado de facturas</h2>
        {loading ? (
          <div className="loading">Cargando...</div>
        ) : facturas.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Período</th>
                    <th>Fecha</th>
                    <th>Monto</th>
                    <th>Detalle</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {facturas.map((f) => {
                    const user = users.find((u) => u.id === f.usuario_id);
                    return (
                      <tr key={f.id}>
                        <td>{user ? `${user.email} — ${user.nombre}` : f.usuario_id.slice(0, 8) + '…'}</td>
                        <td>{f.periodo}</td>
                        <td>{new Date(f.fecha + 'T00:00:00').toLocaleDateString()}</td>
                        <td>${Number(f.monto).toLocaleString()}</td>
                        <td>{f.detalle}</td>
                        <td>{f.estado}</td>
                      <td>
                        <button
                          className="btn btn-ghost"
                          disabled={f.estado === 'abonada'}
                          onClick={() => handleAbonar(f.id)}
                        >
                          Abonar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay facturas cargadas.</p>
        )}
      </div>
    </div>
  );
}
