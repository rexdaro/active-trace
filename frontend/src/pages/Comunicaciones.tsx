import { useEffect, useState } from 'react';
import api from '../services/api';

interface Materia {
  id: number;
  nombre: string;
}

interface Comunicacion {
  id: number;
  destino: string;
  asunto: string;
  estado: string;
  created_at: string;
}

export default function Comunicaciones() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [asunto, setAsunto] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const [comunicaciones, setComunicaciones] = useState<Comunicacion[]>([]);
  const [activeTab, setActiveTab] = useState<'enviar' | 'tracking'>('enviar');
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingSend, setLoadingSend] = useState(false);
  const [trackingLoaded, setTrackingLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'));
  }, []);

  useEffect(() => {
    if (activeTab !== 'tracking') return;
    api
      .get('/api/v1/comunicaciones')
      .then((res) => {
        setComunicaciones(Array.isArray(res.data) ? res.data : []);
        setTrackingLoaded(true);
        setError(null);
      })
      .catch(() => {
        setError('Error al cargar comunicaciones');
        setTrackingLoaded(true);
      });
  }, [activeTab]);

  async function handlePreview() {
    if (!materiaId || !mensaje) return;
    setLoadingPreview(true);
    setError(null);
    try {
      const res = await api.get('/api/v1/comunicaciones/preview', {
        params: { materia_id: materiaId, mensaje },
      });
      setPreview(res.data.preview || res.data.contenido || JSON.stringify(res.data));
    } catch {
      setError('Error al generar preview');
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleSend() {
    if (!materiaId || !mensaje) return;
    setLoadingSend(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/comunicaciones', {
        materia_id: Number(materiaId),
        asunto,
        mensaje,
      });
      setSuccess('Comunicación enviada correctamente');
      setAsunto('');
      setMensaje('');
      setPreview(null);
    } catch {
      setError('Error al enviar comunicación');
    } finally {
      setLoadingSend(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Comunicaciones</h1>
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

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'enviar' ? 'active' : ''}`}
          onClick={() => setActiveTab('enviar')}
        >
          Enviar comunicación
        </button>
        <button
          className={`tab ${activeTab === 'tracking' ? 'active' : ''}`}
          onClick={() => setActiveTab('tracking')}
        >
          Tracking
        </button>
      </div>

      {activeTab === 'enviar' && (
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}
            >
              Materia
            </label>
            <select
              value={materiaId}
              onChange={(e) => setMateriaId(e.target.value)}
              style={{ maxWidth: '400px' }}
            >
              <option value="">Seleccionar materia...</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nombre}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}
            >
              Asunto
            </label>
            <input
              type="text"
              value={asunto}
              onChange={(e) => setAsunto(e.target.value)}
              placeholder="Asunto del mensaje"
              style={{ maxWidth: '400px' }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}
            >
              Mensaje
            </label>
            <textarea
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
              placeholder="Escribí el mensaje..."
              rows={5}
              style={{ maxWidth: '600px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <button
              className="btn btn-ghost"
              onClick={handlePreview}
              disabled={!materiaId || !mensaje || loadingPreview}
            >
              {loadingPreview ? 'Generando...' : 'Vista previa'}
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSend}
              disabled={!materiaId || !mensaje || loadingSend}
            >
              {loadingSend ? 'Enviando...' : 'Enviar a atrasados'}
            </button>
          </div>

          {preview && (
            <div
              style={{
                background: '#f8fafc',
                padding: '1rem',
                borderRadius: '0.375rem',
                border: '1px solid var(--border)',
              }}
            >
              <h3 style={{ marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                Vista previa
              </h3>
              <pre style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                {preview}
              </pre>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tracking' && (
        <div className="card">
          {!trackingLoaded && <div className="loading">Cargando...</div>}
          {trackingLoaded && comunicaciones.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Destino</th>
                    <th>Asunto</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {comunicaciones.map((c) => (
                    <tr key={c.id}>
                      <td>{c.id}</td>
                      <td>{c.destino}</td>
                      <td>{c.asunto}</td>
                      <td>{c.estado}</td>
                      <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            trackingLoaded && (
              <p style={{ color: 'var(--text-muted)' }}>
                No hay comunicaciones enviadas.
              </p>
            )
          )}
        </div>
      )}
    </div>
  );
}
