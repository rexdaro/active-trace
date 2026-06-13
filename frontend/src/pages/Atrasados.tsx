import { useEffect, useState } from 'react';
import api from '../services/api';

interface Materia {
  id: number;
  nombre: string;
}

interface Atrasado {
  id: number;
  alumno: string;
  materia: string;
  actividades_atrasadas: number;
}

interface RankingItem {
  alumno: string;
  actividades_aprobadas: number;
  promedio: number;
}

export default function Atrasados() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'atrasados' | 'ranking' | 'reportes'>(
    'atrasados'
  );
  const [atrasados, setAtrasados] = useState<Atrasado[]>([]);
  const [ranking, setRanking] = useState<RankingItem[]>([]);
  const [reportes, setReportes] = useState<string>('');
  const [loadedTabs, setLoadedTabs] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'));
  }, []);

  useEffect(() => {
    if (!materiaId) return;

    const tabKey = `${materiaId}-${activeTab}`;

    if (activeTab === 'atrasados') {
      api
        .get(`/api/v1/analisis/atrasados?materia_id=${materiaId}`)
        .then((res) => {
          setAtrasados(Array.isArray(res.data) ? res.data : []);
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        })
        .catch(() => {
          setError('Error al cargar atrasados');
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        });
    }

    if (activeTab === 'ranking') {
      api
        .get(`/api/v1/analisis/ranking?materia_id=${materiaId}`)
        .then((res) => {
          setRanking(Array.isArray(res.data) ? res.data : []);
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        })
        .catch(() => {
          setError('Error al cargar ranking');
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        });
    }

    if (activeTab === 'reportes') {
      api
        .get(`/api/v1/analisis/reportes?materia_id=${materiaId}`)
        .then((res) => {
          setReportes(
            typeof res.data === 'string'
              ? res.data
              : JSON.stringify(res.data, null, 2)
          );
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        })
        .catch(() => {
          setError('Error al cargar reportes');
          setLoadedTabs((prev) => ({ ...prev, [tabKey]: true }));
        });
    }
  }, [materiaId, activeTab]);

  function handleExport() {
    const data =
      activeTab === 'atrasados'
        ? atrasados
        : activeTab === 'ranking'
          ? ranking
          : reportes;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeTab}-${materiaId || 'todas'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Atrasados y Reportes</h1>
      </div>

      {error && <div className="error-message">{error}</div>}

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
          className={`tab ${activeTab === 'atrasados' ? 'active' : ''}`}
          onClick={() => setActiveTab('atrasados')}
        >
          Atrasados
        </button>
        <button
          className={`tab ${activeTab === 'ranking' ? 'active' : ''}`}
          onClick={() => setActiveTab('ranking')}
        >
          Ranking
        </button>
        <button
          className={`tab ${activeTab === 'reportes' ? 'active' : ''}`}
          onClick={() => setActiveTab('reportes')}
        >
          Reportes
        </button>
      </div>

      <div className="card">
        {!materiaId && (
          <p style={{ color: 'var(--text-muted)' }}>
            Seleccioná una materia para ver los datos.
          </p>
        )}

        {!loadedTabs[`${materiaId}-${activeTab}`] && materiaId && <div className="loading">Cargando...</div>}

        {loadedTabs[`${materiaId}-${activeTab}`] && materiaId && activeTab === 'atrasados' && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>
                Exportar JSON
              </button>
            </div>
            {atrasados.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Alumno</th>
                      <th>Materia</th>
                      <th>Actividades atrasadas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {atrasados.map((a) => (
                      <tr key={a.id}>
                        <td>{a.alumno}</td>
                        <td>{a.materia}</td>
                        <td>{a.actividades_atrasadas}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>
                No hay alumnos atrasados.
              </p>
            )}
          </>
        )}

        {loadedTabs[`${materiaId}-${activeTab}`] && materiaId && activeTab === 'ranking' && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>
                Exportar JSON
              </button>
            </div>
            {ranking.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Alumno</th>
                      <th>Actividades aprobadas</th>
                      <th>Promedio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranking.map((r, i) => (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        <td>{r.alumno}</td>
                        <td>{r.actividades_aprobadas}</td>
                        <td>{r.promedio}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>Sin datos de ranking.</p>
            )}
          </>
        )}

        {loadedTabs[`${materiaId}-${activeTab}`] && materiaId && activeTab === 'reportes' && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>
                Exportar JSON
              </button>
            </div>
            <pre
              style={{
                background: '#f8fafc',
                padding: '1rem',
                borderRadius: '0.375rem',
                overflowX: 'auto',
                fontSize: '0.875rem',
              }}
            >
              {reportes || 'Sin datos de reportes.'}
            </pre>
          </>
        )}
      </div>
    </div>
  );
}
