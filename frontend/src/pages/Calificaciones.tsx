import { useEffect, useState, useRef } from 'react';
import api from '../services/api';

interface Materia {
  id: string;
  name: string;
  code: string;
}

interface CalificacionItem {
  id: string;
  entrada_padron_id: string;
  materia_id: string;
  actividad: string;
  nota_numerica: number | null;
  nota_textual: string | null;
  aprobado: boolean;
  origen: string;
}

export default function Calificaciones() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [calificaciones, setCalificaciones] = useState<CalificacionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [umbral, setUmbral] = useState(60);
  const [activeTab, setActiveTab] = useState<'importar' | 'umbral'>('importar');
  const [loading, setLoading] = useState(true);
  const [loadingCalifs, setLoadingCalifs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Preview state
  const [previewToken, setPreviewToken] = useState<string | null>(null);
  const [actividades, setActividades] = useState<{ nombre: string; tipo: string }[]>([]);
  const [seleccionadas, setSeleccionadas] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    api
      .get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!materiaId) return;
    setLoadingCalifs(true);
    setError(null);
    api
      .get(`/api/v1/materias/${materiaId}/calificaciones?limit=200`)
      .then((res) => {
        const data = res.data;
        setCalificaciones(data.calificaciones ?? []);
        setTotal(data.total ?? 0);
      })
      .catch(() => setError('Error al cargar calificaciones'))
      .finally(() => setLoadingCalifs(false));
  }, [materiaId]);

  useEffect(() => {
    if (!materiaId) return;
    api
      .get(`/api/v1/materias/${materiaId}/umbral`)
      .then((res) => setUmbral(res.data.umbral_pct ?? 60))
      .catch(() => {});
  }, [materiaId]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !materiaId) return;

    setError(null);
    setSuccess(null);
    setPreviewToken(null);
    setActividades([]);
    setSeleccionadas([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post(`/api/v1/materias/${materiaId}/calificaciones/preview`, formData);
      const data = res.data;
      setPreviewToken(data.preview_token);
      setActividades(data.actividades_detectadas ?? []);
      setSeleccionadas((data.actividades_detectadas ?? []).map((a: any) => a.nombre));
    } catch {
      setError('Error al procesar el archivo');
    }
  }

  async function handleConfirmImport() {
    if (!previewToken || !materiaId) return;
    setImporting(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post(`/api/v1/materias/${materiaId}/calificaciones/confirm`, {
        preview_token: previewToken,
        actividades_seleccionadas: seleccionadas,
      });
      setSuccess('Calificaciones importadas correctamente');
      setPreviewToken(null);
      setActividades([]);
      // Reload
      const res = await api.get(`/api/v1/materias/${materiaId}/calificaciones?limit=200`);
      setCalificaciones(res.data.calificaciones ?? []);
      setTotal(res.data.total ?? 0);
    } catch {
      setError('Error al confirmar la importación');
    } finally {
      setImporting(false);
    }
  }

  async function handleSaveUmbral() {
    if (!materiaId) return;
    setError(null);
    setSuccess(null);
    try {
      await api.put(`/api/v1/materias/${materiaId}/umbral`, {
        umbral_pct: Math.round(umbral),
      });
      setSuccess('Umbral actualizado');
    } catch {
      setError('Error al guardar umbral');
    }
  }

  function resetPreview() {
    setPreviewToken(null);
    setActividades([]);
    setSeleccionadas([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function toggleActividad(nombre: string) {
    setSeleccionadas((prev) =>
      prev.includes(nombre) ? prev.filter((a) => a !== nombre) : [...prev, nombre]
    );
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Calificaciones</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="card">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Materia</label>
        <select
          value={materiaId}
          onChange={(e) => { setMateriaId(e.target.value); resetPreview(); }}
          style={{ maxWidth: '400px' }}
        >
          <option value="">Seleccionar materia...</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'importar' ? 'active' : ''}`} onClick={() => setActiveTab('importar')}>
          Importar calificaciones
        </button>
        <button className={`tab ${activeTab === 'umbral' ? 'active' : ''}`} onClick={() => setActiveTab('umbral')}>
          Configurar umbral
        </button>
      </div>

      {activeTab === 'importar' && materiaId && (
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Importar desde Moodle</h3>

          {!previewToken && (
            <div>
              <p style={{ marginBottom: '0.75rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Seleccioná el archivo CSV con las calificaciones de Moodle.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
              />
            </div>
          )}

          {previewToken && actividades.length > 0 && (
            <div>
              <p style={{ marginBottom: '0.75rem', fontWeight: 600 }}>Actividades detectadas:</p>
              {actividades.map((act) => (
                <label
                  key={act.nombre}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={seleccionadas.includes(act.nombre)}
                    onChange={() => toggleActividad(act.nombre)}
                    style={{ width: 'auto' }}
                  />
                  {act.nombre}
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    ({act.tipo})
                  </span>
                </label>
              ))}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button className="btn btn-primary" onClick={handleConfirmImport} disabled={importing || seleccionadas.length === 0}>
                  {importing ? 'Importando...' : 'Confirmar importación'}
                </button>
                <button className="btn btn-ghost" onClick={resetPreview}>
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'importar' && materiaId && (
        <div className="card">
          {loadingCalifs ? (
            <div className="loading">Cargando calificaciones...</div>
          ) : calificaciones.length > 0 ? (
            <>
              <p style={{ marginBottom: '0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {total} calificaciones
              </p>
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Actividad</th>
                      <th>Nota numérica</th>
                      <th>Nota textual</th>
                      <th>Aprobado</th>
                      <th>Origen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calificaciones.slice(0, 50).map((c) => (
                      <tr key={c.id}>
                        <td>{c.actividad}</td>
                        <td>{c.nota_numerica ?? '—'}</td>
                        <td>{c.nota_textual ?? '—'}</td>
                        <td>
                          <span style={{
                            display: 'inline-block',
                            width: '10px', height: '10px',
                            borderRadius: '50%',
                            background: c.aprobado ? 'var(--success)' : 'var(--danger)',
                            marginRight: '0.3rem',
                          }} />
                          {c.aprobado ? 'Sí' : 'No'}
                        </td>
                        <td>{c.origen}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {calificaciones.length > 50 && (
                <p style={{ marginTop: '0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  Mostrando 50 de {total} calificaciones
                </p>
              )}
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No hay calificaciones para esta materia.</p>
          )}
        </div>
      )}

      {activeTab === 'umbral' && materiaId && (
        <div className="card" style={{ maxWidth: '400px' }}>
          <h3 style={{ marginBottom: '1rem' }}>Umbral de aprobación</h3>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
            Porcentaje mínimo para aprobar
          </label>
          <input
            type="number"
            min={1}
            max={100}
            value={umbral}
            onChange={(e) => setUmbral(Number(e.target.value))}
            style={{ marginBottom: '1rem' }}
          />
          <button className="btn btn-primary" onClick={handleSaveUmbral}>
            Guardar
          </button>
        </div>
      )}

      {!materiaId && (
        <div className="card">
          <p style={{ color: 'var(--text-muted)' }}>Seleccioná una materia para empezar.</p>
        </div>
      )}
    </div>
  );
}
