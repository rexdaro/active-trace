import { useEffect, useState } from 'react';
import api from '../services/api';

interface Factura {
  id: number;
  docente: string;
  periodo: string;
  detalle: string;
  monto: number;
  estado: string;
  created_at: string;
}

export default function Facturas() {
  const [facturas, setFacturas] = useState<Factura[]>([]);
  const [detalle, setDetalle] = useState('');
  const [monto, setMonto] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadFacturas();
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
    if (!detalle || !monto) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/facturas', { detalle, monto: Number(monto) });
      setSuccess('Factura cargada correctamente');
      setDetalle('');
      setMonto('');
      loadFacturas();
    } catch {
      setError('Error al cargar factura');
    } finally {
      setSaving(false);
    }
  }

  async function handleAbonar(id: number) {
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
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Detalle</label>
            <textarea
              value={detalle}
              onChange={(e) => setDetalle(e.target.value)}
              placeholder="Detalle de la factura"
              rows={3}
              required
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Monto</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="0.00"
              required
              style={{ maxWidth: '200px' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Archivo (opcional)</label>
            <input type="file" disabled />
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Carga de archivo próximamente
            </p>
          </div>
          <button className="btn btn-primary" type="submit" disabled={saving}>
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
                  <th>Docente</th>
                  <th>Período</th>
                  <th>Detalle</th>
                  <th>Monto</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {facturas.map((f) => (
                  <tr key={f.id}>
                    <td>{f.docente}</td>
                    <td>{f.periodo}</td>
                    <td>{f.detalle}</td>
                    <td>${f.monto.toLocaleString()}</td>
                    <td>{f.estado}</td>
                    <td>{new Date(f.created_at).toLocaleDateString()}</td>
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
                ))}
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
