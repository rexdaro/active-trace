import { useEffect, useState } from 'react';
import api from '../services/api';

interface Carrera {
  id: string;
  name: string;
  code: string;
}

interface Cohorte {
  id: string;
  name: string;
  carrera_id: string;
}

interface Materia {
  id: string;
  name: string;
  code: string;
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

  const [editId, setEditId] = useState<string | null>(null);
  const [formName, setFormName] = useState('');
  const [formCode, setFormCode] = useState('');
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
    setFormName('');
    setFormCode('');
    setFormCarreraId('');
  }

  function startEdit(item: Carrera | Cohorte | Materia) {
    setEditId(item.id);
    setFormName(item.name);
    if ('code' in item) setFormCode(item.code);
    if ('carrera_id' in item) setFormCarreraId((item as Cohorte).carrera_id);
  }

  function getPayload(): Record<string, unknown> {
    if (activeTab === 'carreras' || activeTab === 'materias') {
      return { name: formName, code: formCode };
    }
    // cohortes
    return { name: formName, carrera_id: formCarreraId || selectedCarreraId };
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const base = activeTab === 'cohortes' ? '/api/cohortes' : `/api/${activeTab}`;
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

  async function handleDelete(id: string) {
    if (!confirm('¿Confirmás eliminar?')) return;
    setError(null);
    setSuccess(null);
    try {
      const base = activeTab === 'cohortes' ? '/api/cohortes' : `/api/${activeTab}`;
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
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      )}

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>
          {(() => {
            const isCarrera = activeTab === 'carreras';
            const isMateria = activeTab === 'materias';
            const article = (isCarrera || isMateria) ? 'Nueva' : 'Nuevo';
            const label = isCarrera ? 'carrera' : activeTab === 'cohortes' ? 'cohorte' : 'materia';
            return `${editId ? 'Editar' : article} ${label}`;
          })()}
        </h2>
        <form onSubmit={handleSave} style={{ maxWidth: '500px' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Nombre</label>
            <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)} required />
          </div>
          {(activeTab === 'carreras' || activeTab === 'materias') && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Código</label>
              <input type="text" value={formCode} onChange={(e) => setFormCode(e.target.value)} />
            </div>
          )}
          {activeTab === 'cohortes' && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Carrera</label>
              <select value={formCarreraId || selectedCarreraId} onChange={(e) => setFormCarreraId(e.target.value)} required>
                <option value="">Seleccionar carrera...</option>
                {carreras.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
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
                    {activeTab === 'cohortes' && <th>Carrera ID</th>}
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.name}</td>
                      {(activeTab === 'carreras' || activeTab === 'materias') && <td>{(item as Carrera | Materia).code || '—'}</td>}
                      {activeTab === 'cohortes' && <td>{(item as Cohorte).carrera_id}</td>}
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn btn-ghost" onClick={() => startEdit(item)}>Editar</button>
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
