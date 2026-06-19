import { useEffect, useState } from 'react';
import api from '../services/api';

interface Liquidacion {
  id: number;
  docente: string;
  rol: string;
  base: number;
  plus: number;
  total: number;
  estado: string;
  periodo: string;
}

interface Kpis {
  totalAPagar: number;
  cantidadDocentes: number;
  promedio: number;
}

export default function Liquidaciones() {
  const [activeTab, setActiveTab] = useState<'general' | 'nexo' | 'factura' | 'historial'>('general');
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [historial, setHistorial] = useState<Liquidacion[]>([]);
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [loading, setLoading] = useState(false);
  const [historialLoading, setHistorialLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === 'historial') {
      loadHistorial();
    } else {
      loadLiquidaciones();
    }
  }, [activeTab, periodo]);

  async function loadLiquidaciones() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/liquidaciones', {
        params: { periodo },
      });
      const data = Array.isArray(res.data) ? res.data : res.data.items ?? res.data.liquidaciones ?? [];
      setLiquidaciones(data);
      const total = data.reduce((s: number, l: Liquidacion) => s + l.total, 0);
      setKpis({
        totalAPagar: total,
        cantidadDocentes: data.length,
        promedio: data.length > 0 ? total / data.length : 0,
      });
    } catch {
      setError('Error al cargar liquidaciones');
    } finally {
      setLoading(false);
    }
  }

  async function loadHistorial() {
    setHistorialLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/liquidaciones/historial');
      setHistorial(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar historial');
    } finally {
      setHistorialLoading(false);
    }
  }

  async function handleCalcular() {
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/liquidaciones/calcular', { periodo });
      setSuccess('Liquidaciones calculadas correctamente');
      loadLiquidaciones();
    } catch {
      setError('Error al calcular liquidaciones');
    }
  }

  async function handleCerrar(id: number) {
    if (!confirm('¿Confirmás cerrar esta liquidación?')) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/api/v1/liquidaciones/${id}/cerrar`);
      setSuccess('Liquidación cerrada correctamente');
      loadLiquidaciones();
    } catch {
      setError('Error al cerrar liquidación');
    }
  }

  const segmentacion = activeTab === 'historial' ? null : activeTab;

  function renderKpis() {
    if (!kpis) return null;
    return (
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-value">${kpis.totalAPagar.toLocaleString()}</div>
          <div className="stat-label">Total a pagar</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{kpis.cantidadDocentes}</div>
          <div className="stat-label">Cantidad docentes</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${Math.round(kpis.promedio).toLocaleString()}</div>
          <div className="stat-label">Promedio</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Liquidaciones</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'general' ? 'active' : ''}`} onClick={() => setActiveTab('general')}>General</button>
        <button className={`tab ${activeTab === 'nexo' ? 'active' : ''}`} onClick={() => setActiveTab('nexo')}>NEXO</button>
        <button className={`tab ${activeTab === 'factura' ? 'active' : ''}`} onClick={() => setActiveTab('factura')}>Factura</button>
        <button className={`tab ${activeTab === 'historial' ? 'active' : ''}`} onClick={() => setActiveTab('historial')}>Historial</button>
      </div>

      {activeTab !== 'historial' && (
        <div className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ maxWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Período</label>
            <input type="month" value={periodo} onChange={(e) => setPeriodo(e.target.value)} />
          </div>
          <button className="btn btn-primary" onClick={handleCalcular}>Calcular liquidación</button>
        </div>
      )}

      {activeTab !== 'historial' && renderKpis()}

      {activeTab !== 'historial' && (
        <div className="card">
          {loading ? (
            <div className="loading">Cargando...</div>
          ) : liquidaciones.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Docente</th>
                    <th>Rol</th>
                    <th>Base</th>
                    <th>Plus</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {liquidaciones.map((l) => (
                    <tr key={l.id}>
                      <td>{l.docente}</td>
                      <td>{l.rol}</td>
                      <td>${l.base.toLocaleString()}</td>
                      <td>${l.plus.toLocaleString()}</td>
                      <td><strong>${l.total.toLocaleString()}</strong></td>
                      <td>{l.estado}</td>
                      <td>
                        <button
                          className="btn btn-ghost"
                          disabled={l.estado === 'cerrada'}
                          onClick={() => handleCerrar(l.id)}
                        >
                          Cerrar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No hay liquidaciones para este período.</p>
          )}
        </div>
      )}

      {activeTab === 'historial' && (
        <div className="card">
          {historialLoading ? (
            <div className="loading">Cargando...</div>
          ) : historial.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Docente</th>
                    <th>Rol</th>
                    <th>Base</th>
                    <th>Plus</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Período</th>
                  </tr>
                </thead>
                <tbody>
                  {historial.map((l) => (
                    <tr key={l.id}>
                      <td>{l.docente}</td>
                      <td>{l.rol}</td>
                      <td>${l.base.toLocaleString()}</td>
                      <td>${l.plus.toLocaleString()}</td>
                      <td><strong>${l.total.toLocaleString()}</strong></td>
                      <td>{l.estado}</td>
                      <td>{l.periodo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No hay historial de liquidaciones.</p>
          )}
        </div>
      )}
    </div>
  );
}
