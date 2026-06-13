import { useEffect, useState } from 'react';
import api from '../services/api';

interface SalarioBase {
  id: number;
  rol: string;
  monto: number;
  vigencia_desde: string;
  vigencia_hasta: string;
}

interface SalarioPlus {
  id: number;
  grupo: string;
  rol: string;
  monto: number;
  vigencia_desde: string;
  vigencia_hasta: string;
}

export default function Salarios() {
  const [bases, setBases] = useState<SalarioBase[]>([]);
  const [pluses, setPluses] = useState<SalarioPlus[]>([]);
  const [activeTab, setActiveTab] = useState<'base' | 'plus'>('base');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Base form
  const [baseRol, setBaseRol] = useState('');
  const [baseMonto, setBaseMonto] = useState('');
  const [baseDesde, setBaseDesde] = useState('');
  const [baseHasta, setBaseHasta] = useState('');

  // Plus form
  const [plusGrupo, setPlusGrupo] = useState('');
  const [plusRol, setPlusRol] = useState('');
  const [plusMonto, setPlusMonto] = useState('');
  const [plusDesde, setPlusDesde] = useState('');
  const [plusHasta, setPlusHasta] = useState('');

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSalarios();
  }, []);

  async function loadSalarios() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/salarios');
      const data = res.data;
      setBases(Array.isArray(data.bases) ? data.bases : []);
      setPluses(Array.isArray(data.pluses) ? data.pluses : []);
    } catch {
      setError('Error al cargar grilla salarial');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateBase(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/salarios/base', {
        rol: baseRol,
        monto: Number(baseMonto),
        vigencia_desde: baseDesde,
        vigencia_hasta: baseHasta || null,
      });
      setSuccess('Salario base creado correctamente');
      setBaseRol('');
      setBaseMonto('');
      setBaseDesde('');
      setBaseHasta('');
      loadSalarios();
    } catch {
      setError('Error al crear salario base');
    } finally {
      setSaving(false);
    }
  }

  async function handleCreatePlus(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/salarios/plus', {
        grupo: plusGrupo,
        rol: plusRol,
        monto: Number(plusMonto),
        vigencia_desde: plusDesde,
        vigencia_hasta: plusHasta || null,
      });
      setSuccess('Plus salarial creado correctamente');
      setPlusGrupo('');
      setPlusRol('');
      setPlusMonto('');
      setPlusDesde('');
      setPlusHasta('');
      loadSalarios();
    } catch {
      setError('Error al crear plus salarial');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Grilla Salarial</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'base' ? 'active' : ''}`} onClick={() => setActiveTab('base')}>Salarios Base</button>
        <button className={`tab ${activeTab === 'plus' ? 'active' : ''}`} onClick={() => setActiveTab('plus')}>Plus Salariales</button>
      </div>

      {activeTab === 'base' && (
        <>
          <div className="card">
            <h2 style={{ marginBottom: '1rem' }}>Nuevo salario base</h2>
            <form onSubmit={handleCreateBase} style={{ maxWidth: '500px' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Rol</label>
                <input type="text" value={baseRol} onChange={(e) => setBaseRol(e.target.value)} placeholder="Ej: Profesor Titular" required />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Monto</label>
                <input type="number" step="0.01" min="0" value={baseMonto} onChange={(e) => setBaseMonto(e.target.value)} placeholder="0.00" required style={{ maxWidth: '200px' }} />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Vigencia desde</label>
                <input type="date" value={baseDesde} onChange={(e) => setBaseDesde(e.target.value)} required style={{ maxWidth: '200px' }} />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Vigencia hasta (opcional)</label>
                <input type="date" value={baseHasta} onChange={(e) => setBaseHasta(e.target.value)} style={{ maxWidth: '200px' }} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? 'Guardando...' : 'Crear salario base'}
              </button>
            </form>
          </div>

          <div className="card">
            <h2 style={{ marginBottom: '1rem' }}>Salarios Base actuales</h2>
            {bases.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Rol</th>
                      <th>Monto</th>
                      <th>Vigencia desde</th>
                      <th>Vigencia hasta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bases.map((b) => (
                      <tr key={b.id}>
                        <td>{b.rol}</td>
                        <td>${b.monto.toLocaleString()}</td>
                        <td>{b.vigencia_desde}</td>
                        <td>{b.vigencia_hasta || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No hay salarios base cargados.</p>
            )}
          </div>
        </>
      )}

      {activeTab === 'plus' && (
        <>
          <div className="card">
            <h2 style={{ marginBottom: '1rem' }}>Nuevo plus salarial</h2>
            <form onSubmit={handleCreatePlus} style={{ maxWidth: '500px' }}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Grupo</label>
                <input type="text" value={plusGrupo} onChange={(e) => setPlusGrupo(e.target.value)} placeholder="Ej: Antigüedad" required />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Rol</label>
                <input type="text" value={plusRol} onChange={(e) => setPlusRol(e.target.value)} placeholder="Ej: Profesor Titular" required />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Monto</label>
                <input type="number" step="0.01" min="0" value={plusMonto} onChange={(e) => setPlusMonto(e.target.value)} placeholder="0.00" required style={{ maxWidth: '200px' }} />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Vigencia desde</label>
                <input type="date" value={plusDesde} onChange={(e) => setPlusDesde(e.target.value)} required style={{ maxWidth: '200px' }} />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Vigencia hasta (opcional)</label>
                <input type="date" value={plusHasta} onChange={(e) => setPlusHasta(e.target.value)} style={{ maxWidth: '200px' }} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? 'Guardando...' : 'Crear plus salarial'}
              </button>
            </form>
          </div>

          <div className="card">
            <h2 style={{ marginBottom: '1rem' }}>Plus Salariales actuales</h2>
            {pluses.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Grupo</th>
                      <th>Rol</th>
                      <th>Monto</th>
                      <th>Vigencia desde</th>
                      <th>Vigencia hasta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pluses.map((p) => (
                      <tr key={p.id}>
                        <td>{p.grupo}</td>
                        <td>{p.rol}</td>
                        <td>${p.monto.toLocaleString()}</td>
                        <td>{p.vigencia_desde}</td>
                        <td>{p.vigencia_hasta || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No hay plus salariales cargados.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
