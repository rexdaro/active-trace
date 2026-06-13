import { useEffect, useState } from 'react';
import api from '../services/api';

interface Equipo {
  id: number;
  materia: string;
  rol: string;
  vigencia: string;
}

export default function EquiposDocentes() {
  const [equipos, setEquipos] = useState<Equipo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/api/v1/equipos')
      .then((res) => setEquipos(Array.isArray(res.data) ? res.data : []))
      .catch(() => setError('Error al cargar equipos'))
      .finally(() => setLoading(false));
  }, []);

  async function handleExport() {
    try {
      const res = await api.get('/api/v1/equipos/export', {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'equipos.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Error al exportar');
    }
  }

  async function handleVigencia(id: number) {
    const nueva = prompt('Nueva vigencia (ej: 2025-06-15):');
    if (!nueva) return;
    try {
      await api.put(`/api/v1/equipos/${id}/vigencia`, { vigencia: nueva });
      setEquipos((prev) =>
        prev.map((e) => (e.id === id ? { ...e, vigencia: nueva } : e))
      );
      setSuccess('Vigencia actualizada');
    } catch {
      setError('Error al actualizar vigencia');
    }
  }

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Equipos docentes</h1>
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
        <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={handleExport}>
            Exportar
          </button>
          <button className="btn btn-ghost" onClick={() => document.getElementById('masiva-form')?.classList.toggle('hidden')}>
            Asignación masiva
          </button>
          <button className="btn btn-ghost" onClick={() => document.getElementById('clonar-form')?.classList.toggle('hidden')}>
            Clonar equipo
          </button>
        </div>

        <div id="masiva-form" className="hidden" style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid var(--border)', borderRadius: '0.375rem' }}>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>Asignación masiva</h3>
          <textarea
            id="masiva-data"
            placeholder='[{"email":"docente@mail.com","materia_id":1,"rol":"PROFESOR"}]'
            rows={4}
            style={{ marginBottom: '0.5rem', fontFamily: 'monospace', fontSize: '0.8rem' }}
          />
          <button
            className="btn btn-primary"
            onClick={async () => {
              const el = document.getElementById('masiva-data') as HTMLTextAreaElement;
              try {
                await api.post('/api/v1/equipos/masiva', JSON.parse(el.value));
                setSuccess('Asignación masiva completada');
                const res = await api.get('/api/v1/equipos');
                setEquipos(Array.isArray(res.data) ? res.data : []);
              } catch {
                setError('Error en asignación masiva');
              }
            }}
          >
            Ejecutar
          </button>
        </div>

        <div id="clonar-form" className="hidden" style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid var(--border)', borderRadius: '0.375rem' }}>
          <h3 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>Clonar equipo</h3>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Desde período</label>
              <input id="clonar-desde" type="text" placeholder="ej: 2024" style={{ maxWidth: '150px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem' }}>Hasta período</label>
              <input id="clonar-hasta" type="text" placeholder="ej: 2025" style={{ maxWidth: '150px' }} />
            </div>
            <button
              className="btn btn-primary"
              onClick={async () => {
                const desde = (document.getElementById('clonar-desde') as HTMLInputElement).value;
                const hasta = (document.getElementById('clonar-hasta') as HTMLInputElement).value;
                try {
                  await api.post('/api/v1/equipos/clonar', { desde, hasta });
                  setSuccess('Equipo clonado correctamente');
                  const res = await api.get('/api/v1/equipos');
                  setEquipos(Array.isArray(res.data) ? res.data : []);
                } catch {
                  setError('Error al clonar equipo');
                }
              }}
            >
              Clonar
            </button>
          </div>
        </div>

        {equipos.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Materia</th>
                  <th>Rol</th>
                  <th>Vigencia</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {equipos.map((e) => (
                  <tr key={e.id}>
                    <td>{e.materia}</td>
                    <td>{e.rol}</td>
                    <td>{e.vigencia}</td>
                    <td>
                      <button
                        className="btn btn-ghost"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                        onClick={() => handleVigencia(e.id)}
                      >
                        Cambiar vigencia
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No hay equipos asignados.</p>
        )}
      </div>
    </div>
  );
}
