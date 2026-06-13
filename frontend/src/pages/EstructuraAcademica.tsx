import { useEffect, useState } from 'react';
import api from '../services/api';

interface Carrera {
  id: number;
  nombre: string;
  codigo?: string;
}

interface Cohorte {
  id: number;
  nombre: string;
  anio: number;
  carrera_id: number;
}

interface Materia {
  id: number;
  nombre: string;
  codigo?: string;
  carrera_id?: number;
}

export default function EstructuraAcademica() {
  const [activeTab, setActiveTab] = useState<'carreras' | 'cohortes' | 'materias'>('carreras');
  const [carreras, setCarreras] = useState<Carrera[]>([]);
  const [cohortes, setCohortes] = useState<Cohorte[]>([]);
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [selectedCarreraId, setSelectedCarreraId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [editId, setEditId] = useState<number | null>(null);
  const [formNombre, setFormNombre] = useState('');
  const [formCodigo, setFormCodigo] = useState('');
  const [formAnio, setFormAnio] = useState('');
  const [formCarreraId, setFormCarreraId] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCarreras();
    loadMaterias();
  }, []);

  useEffect(() => {
    if (selectedCarreraId) loadCohortes();
    else setCohortes([]);
  }, [selectedCarreraId]);

  async function loadCarreras() {
    try {
      const res = await api.get('/api/carreras');
      setCarreras(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar carreras');
    }
  }

  async function loadCohortes() {
    try {
      const res = await api.get(`/api/cohortes?carrera_id=${selectedCarreraId}`);
      setCohortes(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar cohortes');
    }
  }

  async function loadMaterias() {
    try {
      const res = await api.get('/api/materias');
      setMaterias(Array.isArray(res.data) ? res.data : res.data.items ?? []);
    } catch {
      setError('Error al cargar materias');
    }
  }

  useEffect(() => {
    setLoading(false);
  }, [carreras, cohortes, materias]);

  function resetForm() {
    setEditId(null);
    setFormNombre('');
    setFormCodigo('');
    setFormAnio('');
    setFormCarreraId('');
  }

  function startEdit(item: Carrera | Cohorte | Materia, type: string) {
    setEditId(item.id);
    setFormNombre(item.nombre);
    if (type === 'carrera') {
      setFormCodigo((item as Carrera).codigo || '');
    } else if (type === 'cohorte') {
      setFormAnio(String((item as Cohorte).anio));
      setFormCarreraId(String((item as Cohorte).carrera_id));
    } else if (type === 'materia') {
      setFormCodigo((item as Materia).codigo || '');
      setFormCarreraId(String((item as Materia).carrera_id || ''));
    }
  }

  function getApiBase(): string {
    if (activeTab === 'cohortes') return '/api/cohortes';
    return `/api/${activeTab}`;
  }

  function getPayload(): Record<string, unknown> {
    const payload: Record<string, unknown> = { nombre: formNombre };
    if (activeTab === 'carreras' || activeTab === 'materias') {
      payload.codigo = formCodigo;
    }
    if (activeTab === 'cohortes') {
      payload.anio = Number(formAnio);
      payload.carrera_id = Number(selectedCarreraId || formCarreraId);
    }
    if (activeTab === 'materias' && formCarreraId) {
      payload.carrera_id = Number(formCarreraId);
    }
    return payload;
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const base = getApiBase();
      const payload = getPayload();
      if (editId) {
        await api.put(`${base}/${editId}`, payload);
        setSuccess('Actualizado correctamente');
      } else {
        await api.post(base, payload);
        setSuccess('Creado correctamente');
      }
      resetForm();
      if (activeTab === 'carreras') loadCarreras();
      else if (activeTab === 'cohortes') loadCohortes();
      else loadMaterias();
    } catch {
      setError('Error al guardar');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('¿Confirmás eliminar?')) return;
    setError(null);
    setSuccess(null);
    try {
      const base = getApiBase();
      await api.delete(`${base}/${id}`);
      setSuccess('Eliminado correctamente');
      if (activeTab === 'carreras') loadCarreras();
      else if (activeTab === 'cohortes') loadCohortes();
      else loadMaterias();
    } catch {
      setError('Error al eliminar');
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Estructura Académica</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="error-message" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
          {success}
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${activeTab === 'carreras' ? 'active' : ''}`} onClick={() => { setActiveTab('carreras'); resetForm(); }}>Carreras</button>
        <button className={`tab ${activeTab === 'cohortes' ? 'active' : ''}`} onClick={() => { setActiveTab('cohortes'); resetForm(); }}>Cohortes</button>
        <button className={`tab ${activeTab === 'materias' ? 'active' : ''}`} onClick={() => { setActiveTab('materias'); resetForm(); }}>Materias</button>
      </div>

      {activeTab === 'cohortes' && (
        <div className="card">
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Carrera</label>
          <select value={selectedCarreraId} onChange={(e) => setSelectedCarreraId(e.target.value)} style={{ maxWidth: '400px' }}>
            <option value="">Seleccionar carrera...</option>
            {carreras.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
      )}

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>
          {editId ? 'Editar' : 'Nuevo'} {activeTab === 'carreras' ? 'carrera' : activeTab === 'cohortes' ? 'cohorte' : 'materia'}
        </h2>
        <form onSubmit={handleSave} style={{ maxWidth: '500px' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Nombre</label>
            <input type="text" value={formNombre} onChange={(e) => setFormNombre(e.target.value)} required />
          </div>
          {(activeTab === 'carreras' || activeTab === 'materias') && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Código</label>
              <input type="text" value={formCodigo} onChange={(e) => setFormCodigo(e.target.value)} />
            </div>
          )}
          {activeTab === 'cohortes' && (
            <>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Año</label>
                <input type="number" value={formAnio} onChange={(e) => setFormAnio(e.target.value)} required style={{ maxWidth: '200px' }} />
              </div>
              {!selectedCarreraId && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Carrera</label>
                  <select value={formCarreraId} onChange={(e) => setFormCarreraId(e.target.value)} required>
                    <option value="">Seleccionar carrera...</option>
                    {carreras.map((c) => (
                      <option key={c.id} value={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}
          {activeTab === 'materias' && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Carrera</label>
              <select value={formCarreraId} onChange={(e) => setFormCarreraId(e.target.value)}>
                <option value="">Sin carrera</option>
                {carreras.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>
          )}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Guardando...' : editId ? 'Actualizar' : 'Crear'}
            </button>
            {editId && (
              <button className="btn btn-ghost" type="button" onClick={resetForm}>Cancelar</button>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>
          {activeTab === 'carreras' ? 'Carreras' : activeTab === 'cohortes' ? 'Cohortes' : 'Materias'}
        </h2>
        {(() => {
          const items = activeTab === 'carreras' ? carreras : activeTab === 'cohortes' ? cohortes : materias;
          if (items.length === 0) {
            return <p style={{ color: 'var(--text-muted)' }}>No hay datos.</p>;
          }
          return (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Nombre</th>
                    {(activeTab === 'carreras' || activeTab === 'materias') && <th>Código</th>}
                    {activeTab === 'cohortes' && <th>Año</th>}
                    {activeTab === 'cohortes' && <th>Carrera ID</th>}
                    {activeTab === 'materias' && <th>Carrera ID</th>}
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.nombre}</td>
                      {(activeTab === 'carreras' || activeTab === 'materias') && <td>{(item as Carrera | Materia).codigo || '—'}</td>}
                      {activeTab === 'cohortes' && <td>{(item as Cohorte).anio}</td>}
                      {activeTab === 'cohortes' && <td>{(item as Cohorte).carrera_id}</td>}
                      {activeTab === 'materias' && <td>{(item as Materia).carrera_id || '—'}</td>}
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn btn-ghost" onClick={() => startEdit(item, activeTab)}>Editar</button>
                          <button className="btn btn-danger" onClick={() => handleDelete(item.id)}>Eliminar</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
