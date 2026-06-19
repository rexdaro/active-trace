import { useEffect, useState } from 'react';
import api from '../services/api';

interface Materia {
  id: string;
  name: string;
  code: string;
}

interface AlumnoAtrasado {
  entrada_padron_id: string;
  nombre: string;
  apellidos: string;
  comision: string | null;
  actividades_faltantes: string[];
  actividades_desaprobadas: string[];
  motivo: string;
}

interface RankingEntry {
  posicion: number;
  nombre: string;
  apellidos: string;
  comision: string | null;
  actividades_aprobadas: number;
  total_actividades: number;
}

interface ReporteMateria {
  sin_datos?: boolean;
  mensaje?: string;
  total_alumnos: number;
  total_actividades: number;
  total_calificaciones: number;
  aprobados: number;
  no_aprobados: number;
  porcentaje_aprobacion: number;
  por_actividad: ActividadReporte[];
}

interface ActividadReporte {
  actividad: string;
  total: number;
  aprobados: number;
  no_aprobados: number;
  porcentaje_aprobacion: number;
}

export default function Atrasados() {
  const [materias, setMaterias] = useState<Materia[]>([]);
  const [materiaId, setMateriaId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'atrasados' | 'ranking' | 'reportes'>('atrasados');
  const [atrasados, setAtrasados] = useState<AlumnoAtrasado[]>([]);
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [reporte, setReporte] = useState<ReporteMateria | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/api/materias')
      .then((res) => setMaterias(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar materias'));
  }, []);

  useEffect(() => {
    if (!materiaId) return;
    setLoading(true);
    setError(null);

    const path = activeTab === 'reportes'
      ? `/api/v1/analisis/materias/${materiaId}/reporte`
      : `/api/v1/analisis/materias/${materiaId}/${activeTab}`;

    api.get(path)
      .then((res) => {
        if (activeTab === 'atrasados') setAtrasados(res.data.atrasados ?? []);
        else if (activeTab === 'ranking') setRanking(res.data.ranking ?? []);
        else setReporte(res.data);
      })
      .catch((err) => {
        const msg = err?.response?.data?.detail || err?.message || 'Error al cargar datos';
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [materiaId, activeTab]);

  function handleExport() {
    let data: unknown;
    if (activeTab === 'atrasados') data = atrasados;
    else if (activeTab === 'ranking') data = ranking;
    else data = reporte;

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
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
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Materia</label>
        <select value={materiaId} onChange={(e) => setMateriaId(e.target.value)} style={{ maxWidth: '400px' }}>
          <option value="">Seleccionar materia...</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'atrasados' ? 'active' : ''}`} onClick={() => setActiveTab('atrasados')}>Atrasados</button>
        <button className={`tab ${activeTab === 'ranking' ? 'active' : ''}`} onClick={() => setActiveTab('ranking')}>Ranking</button>
        <button className={`tab ${activeTab === 'reportes' ? 'active' : ''}`} onClick={() => setActiveTab('reportes')}>Reportes</button>
      </div>

      <div className="card">
        {!materiaId && (
          <p style={{ color: 'var(--text-muted)' }}>Seleccioná una materia para ver los datos.</p>
        )}

        {loading && materiaId && <div className="loading">Cargando...</div>}

        {!loading && materiaId && activeTab === 'atrasados' && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>Exportar JSON</button>
            </div>
            {atrasados.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Apellidos</th>
                      <th>Comisión</th>
                      <th>Act. faltantes</th>
                      <th>Act. desaprobadas</th>
                      <th>Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {atrasados.map((a) => (
                      <tr key={a.entrada_padron_id}>
                        <td>{a.nombre}</td>
                        <td>{a.apellidos}</td>
                        <td>{a.comision ?? '—'}</td>
                        <td>{a.actividades_faltantes.join(', ') || '—'}</td>
                        <td>{a.actividades_desaprobadas.join(', ') || '—'}</td>
                        <td>{a.motivo}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No hay alumnos atrasados.</p>
            )}
          </>
        )}

        {!loading && materiaId && activeTab === 'ranking' && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>Exportar JSON</button>
            </div>
            {ranking.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Nombre</th>
                      <th>Apellidos</th>
                      <th>Comisión</th>
                      <th>Act. aprobadas</th>
                      <th>Total actividades</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranking.map((r) => (
                      <tr key={r.posicion}>
                        <td>{r.posicion}</td>
                        <td>{r.nombre}</td>
                        <td>{r.apellidos}</td>
                        <td>{r.comision ?? '—'}</td>
                        <td>{r.actividades_aprobadas}</td>
                        <td>{r.total_actividades}</td>
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

        {!loading && materiaId && activeTab === 'reportes' && reporte && (
          <>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-ghost" onClick={handleExport}>Exportar JSON</button>
            </div>
            {reporte.sin_datos ? (
              <p style={{ color: 'var(--text-muted)' }}>{reporte.mensaje ?? 'Sin datos para esta materia.'}</p>
            ) : (
              <div>
                <div className="card-grid" style={{ marginBottom: '1rem' }}>
                  <div className="stat-card">
                    <div className="stat-value">{reporte.total_alumnos}</div>
                    <div className="stat-label">Alumnos</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{reporte.total_actividades}</div>
                    <div className="stat-label">Actividades</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{reporte.porcentaje_aprobacion.toFixed(1)}%</div>
                    <div className="stat-label">Aprobación</div>
                  </div>
                </div>
                {reporte.por_actividad.length > 0 && (
                  <div style={{ overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Actividad</th>
                          <th>Total</th>
                          <th>Aprobados</th>
                          <th>No aprobados</th>
                          <th>% Aprobación</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reporte.por_actividad.map((a) => (
                          <tr key={a.actividad}>
                            <td>{a.actividad}</td>
                            <td>{a.total}</td>
                            <td>{a.aprobados}</td>
                            <td>{a.no_aprobados}</td>
                            <td>{a.porcentaje_aprobacion.toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
