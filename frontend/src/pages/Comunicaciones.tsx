import { useEffect, useState } from 'react';
import api from '../services/api';

interface Materia {
  id: string;
  name: string;
  code: string;
}

interface Lote {
  lote_id: string;
  materia_id: string;
  total: number;
  pendientes: number;
  enviando: number;
  enviados: number;
  errores: number;
  cancelados: number;
  created_at: string;
}

export default function Comunicaciones() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [asunto, setAsunto] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [activeTab, setActiveTab] = useState<'enviar' | 'tracking'>('enviar');

  // Preview state
  const [previewToken, setPreviewToken] = useState<string | null>(null);
  const [previewItems, setPreviewItems] = useState<any[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingSend, setLoadingSend] = useState(false);
  const [loadingDirect, setLoadingDirect] = useState(false);
  const [step, setStep] = useState<'form' | 'preview'>('form');

  // Tracking state
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [trackingLoaded, setTrackingLoaded] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api.get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'));
  }, []);

  useEffect(() => {
    if (activeTab !== 'tracking') return;
    api.get('/api/v1/comunicaciones/lotes')
      .then((res) => {
        setLotes(res.data.lotes ?? []);
        setTrackingLoaded(true);
      })
      .catch(() => {
        setError('Error al cargar lotes');
        setTrackingLoaded(true);
      });
  }, [activeTab]);

  async function fetchDestinatarios() {
    // Try atrasados first, fallback to all alumnos
    try {
      const atrasadosRes = await api.get(`/api/v1/analisis/materias/${materiaId}/atrasados`);
      const atrasados = atrasadosRes.data?.atrasados ?? [];
      if (atrasados.length > 0) {
        return atrasados.map((a: any) => a.entrada_padron_id);
      }
    } catch { /* ignore — fallback */ }

    try {
      const alumnosRes = await api.get(`/api/v1/padron/${materiaId}/alumnos`);
      const alumnos: any[] = alumnosRes.data ?? [];
      return alumnos.map((a: any) => a.id);
    } catch { /* ignore — fallback */ }

    return [];
  }

  async function doPreview(destinatarios: string[]) {
    const res = await api.post('/api/v1/comunicaciones/preview', {
      destinatarios,
      asunto: asunto || 'Comunicación automática',
      cuerpo: mensaje,
      materia_id: materiaId,
    });
    setPreviewToken(res.data.preview_token);
    setPreviewItems(res.data.items ?? []);
    setStep('preview');
  }

  async function handlePreview() {
    if (!materiaId || !mensaje) return;
    setLoadingPreview(true);
    setError(null);

    try {
      const destinatarios = await fetchDestinatarios();
      if (destinatarios.length === 0) {
        setError('No hay alumnos cargados en el padrón para esta materia. Primero importá alumnos desde Padrón.');
        setLoadingPreview(false);
        return;
      }
      await doPreview(destinatarios);
    } catch {
      setError('Error al generar preview');
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleSendAll() {
    if (!materiaId || !mensaje) return;
    setLoadingDirect(true);
    setError(null);
    setSuccess(null);

    try {
      const destinatarios = await fetchDestinatarios();
      if (destinatarios.length === 0) {
        setError('No hay alumnos cargados en el padrón para esta materia. Primero importá alumnos desde Padrón.');
        setLoadingDirect(false);
        return;
      }
      const resPreview = await api.post('/api/v1/comunicaciones/preview', {
        destinatarios,
        asunto: asunto || 'Comunicación automática',
        cuerpo: mensaje,
        materia_id: materiaId,
      });
      const resConfirm = await api.post('/api/v1/comunicaciones/confirm', {
        preview_token: resPreview.data.preview_token,
      });
      const { cantidad, requiere_aprobacion } = resConfirm.data;
      if (cantidad === 0) {
        setError('No se pudo enviar la comunicación: no hay destinatarios disponibles.');
        setLoadingDirect(false);
        return;
      }
      setSuccess(
        `Comunicación enviada a ${cantidad} destinatario${cantidad !== 1 ? 's' : ''}${requiere_aprobacion ? ' (requiere aprobación)' : ''} correctamente`
      );
      resetForm();
    } catch {
      setError('Error al enviar comunicación');
    } finally {
      setLoadingDirect(false);
    }
  }

  async function handleConfirm() {
    if (!previewToken) return;
    setLoadingSend(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.post('/api/v1/comunicaciones/confirm', {
        preview_token: previewToken,
      });
      const { cantidad, requiere_aprobacion } = res.data;
      if (cantidad === 0) {
        setError('No se pudo enviar la comunicación: no hay destinatarios disponibles.');
        setLoadingSend(false);
        return;
      }
      setSuccess(
        `Comunicación enviada a ${cantidad} destinatario${cantidad !== 1 ? 's' : ''}${requiere_aprobacion ? ' (requiere aprobación)' : ''} correctamente`
      );
      resetForm();
    } catch {
      setError('Error al enviar comunicación');
    } finally {
      setLoadingSend(false);
    }
  }

  function resetForm() {
    setStep('form');
    setPreviewToken(null);
    setPreviewItems([]);
    setAsunto('');
    setMensaje('');
  }

  return (
    <div>
      <div className="page-header">
        <h1>Comunicaciones</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'enviar' ? 'active' : ''}`} onClick={() => { setActiveTab('enviar'); resetForm(); }}>
          Enviar comunicación
        </button>
        <button className={`tab ${activeTab === 'tracking' ? 'active' : ''}`} onClick={() => setActiveTab('tracking')}>
          Tracking
        </button>
      </div>

      {activeTab === 'enviar' && step === 'form' && (
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Materia</label>
            <select value={materiaId} onChange={(e) => setMateriaId(e.target.value)} style={{ maxWidth: '400px' }}>
              <option value="">Seleccionar materia...</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Asunto</label>
            <input type="text" value={asunto} onChange={(e) => setAsunto(e.target.value)}
              placeholder="Asunto del mensaje" style={{ maxWidth: '400px' }} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Mensaje</label>
            <textarea value={mensaje} onChange={(e) => setMensaje(e.target.value)}
              placeholder="Escribí el mensaje..." rows={5} style={{ maxWidth: '600px' }} />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-ghost" onClick={handlePreview}
              disabled={!materiaId || !mensaje || loadingPreview}>
              {loadingPreview ? 'Generando...' : 'Vista previa'}
            </button>
            <button className="btn btn-primary" onClick={handleSendAll}
              disabled={!materiaId || !mensaje || loadingDirect}>
              {loadingDirect ? 'Enviando...' : 'Enviar comunicación'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'enviar' && step === 'preview' && previewToken && (
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Vista previa</h3>
          <p style={{ marginBottom: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {previewItems.length} destinatario{previewItems.length !== 1 ? 's' : ''}
          </p>
          <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '1rem', border: '1px solid var(--border)', borderRadius: '0.375rem' }}>
            {previewItems.map((item: any, i: number) => (
              <div key={item.entrada_padron_id || i} style={{
                padding: '0.6rem 1rem',
                borderBottom: i < previewItems.length - 1 ? '1px solid var(--border)' : 'none',
                fontSize: '0.85rem',
              }}>
                <strong>{item.destinatario}</strong> — {item.nombre}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={handleConfirm} disabled={loadingSend}>
              {loadingSend ? 'Enviando...' : 'Confirmar envío'}
            </button>
            <button className="btn btn-ghost" onClick={resetForm}>Cancelar</button>
          </div>
        </div>
      )}

      {activeTab === 'tracking' && (
        <div className="card">
          {!trackingLoaded && <div className="loading">Cargando...</div>}
          {trackingLoaded && lotes.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Lote ID</th>
                    <th>Total</th>
                    <th>Pendientes</th>
                    <th>Enviando</th>
                    <th>Enviados</th>
                    <th>Errores</th>
                    <th>Cancelados</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {lotes.map((l) => (
                    <tr key={l.lote_id}>
                      <td title={l.lote_id}>{l.lote_id.slice(0, 8)}…</td>
                      <td>{l.total}</td>
                      <td>{l.pendientes}</td>
                      <td>{l.enviando}</td>
                      <td>{l.enviados}</td>
                      <td>{l.errores}</td>
                      <td>{l.cancelados}</td>
                      <td>{new Date(l.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            trackingLoaded && <p style={{ color: 'var(--text-muted)' }}>No hay comunicaciones enviadas.</p>
          )}
        </div>
      )}
    </div>
  );
}
