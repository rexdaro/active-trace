import { useEffect, useState } from 'react';
import api from '../services/api';

interface Materia {
  id: number;
  nombre: string;
}

interface Calificacion {
  id: number;
  alumno: string;
  materia: string;
  nota: number;
  estado: string;
}

export default function Calificaciones() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [calificaciones, setCalificaciones] = useState<Calificacion[]>([]);
  const [umbral, setUmbral] = useState<number>(6);
  const [activeTab, setActiveTab] = useState<'importar' | 'umbral'>('importar');
  const [loadingMaterias, setLoadingMaterias] = useState(true);
  const [califsLoaded, setCalifsLoaded] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'))
      .finally(() => setLoadingMaterias(false));
  }, []);

  useEffect(() => {
    if (!materiaId) return;
    api
      .get(`/api/v1/calificaciones?materia_id=${materiaId}`)
      .then((res) => {
        setCalificaciones(Array.isArray(res.data) ? res.data : []);
        setCalifsLoaded((prev) => ({ ...prev, [materiaId]: true }));
        setError(null);
      })
      .catch(() => {
        setError('Error al cargar calificaciones');
        setCalifsLoaded((prev) => ({ ...prev, [materiaId]: true }));
      });
  }, [materiaId]);

  async function handleImport() {
    if (!materiaId) return;
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/calificaciones/import', {
        materia_id: Number(materiaId),
      });
      setSuccess('Calificaciones importadas correctamente');
      const res = await api.get(
        `/api/v1/calificaciones?materia_id=${materiaId}`
      );
      setCalificaciones(Array.isArray(res.data) ? res.data : []);
    } catch {
      setError('Error al importar calificaciones');
    }
  }

  async function handleSaveUmbral() {
    setError(null);
    setSuccess(null);
    try {
      await api.put('/api/v1/umbral', { valor: umbral });
      setSuccess('Umbral actualizado correctamente');
    } catch {
      setError('Error al guardar umbral');
    }
  }

  if (loadingMaterias) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Calificaciones</h1>
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

      <div className="card">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
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

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'importar' ? 'active' : ''}`}
          onClick={() => setActiveTab('importar')}
        >
          Importar calificaciones
        </button>
        <button
          className={`tab ${activeTab === 'umbral' ? 'active' : ''}`}
          onClick={() => setActiveTab('umbral')}
        >
          Configurar umbral
        </button>
      </div>

      {activeTab === 'importar' && (
        <div className="card">
          <div style={{ marginBottom: '1rem' }}>
            <button
              className="btn btn-primary"
              onClick={handleImport}
              disabled={!materiaId}
            >
              Importar desde Moodle
            </button>
          </div>

          {!califsLoaded[materiaId] && materiaId && <div className="loading">Cargando calificaciones...</div>}

          {califsLoaded[materiaId] && calificaciones.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Alumno</th>
                    <th>Materia</th>
                    <th>Nota</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {calificaciones.map((c) => (
                    <tr key={c.id}>
                      <td>{c.alumno}</td>
                      <td>{c.materia}</td>
                      <td>{c.nota}</td>
                      <td>{c.estado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {califsLoaded[materiaId] && materiaId && calificaciones.length === 0 && (
            <p style={{ color: 'var(--text-muted)' }}>
              No hay calificaciones para esta materia.
            </p>
          )}
        </div>
      )}

      {activeTab === 'umbral' && (
        <div className="card" style={{ maxWidth: '400px' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
            Umbral de aprobación
          </label>
          <input
            type="number"
            min={1}
            max={10}
            step={0.5}
            value={umbral}
            onChange={(e) => setUmbral(Number(e.target.value))}
            style={{ marginBottom: '1rem' }}
          />
          <button className="btn btn-primary" onClick={handleSaveUmbral}>
            Guardar
          </button>
        </div>
      )}
    </div>
  );
}
