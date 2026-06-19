import { useState, useRef, useEffect } from 'react';
import api from '../services/api';

interface ApiError {
  response?: {
    status: number;
    data?: { detail?: string };
  };
}

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export default function AuthPage() {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string; confirmPassword?: string }>({});
  const formRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (formRef.current) {
      formRef.current.classList.remove('auth-fade-in');
      void formRef.current.offsetWidth;
      formRef.current.classList.add('auth-fade-in');
    }
    setError('');
    setSuccess('');
    setFieldErrors({});
  }, [isRegistering]);

  function validate(): boolean {
    const errors: { email?: string; password?: string; confirmPassword?: string } = {};

    if (!email.trim()) {
      errors.email = 'El email es requerido';
    } else if (!validateEmail(email)) {
      errors.email = 'Formato de email inválido';
    }

    if (!password) {
      errors.password = 'La contraseña es requerida';
    } else if (password.length < 6) {
      errors.password = 'Mínimo 6 caracteres';
    }

    if (isRegistering && password !== confirmPassword) {
      errors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function getErrorMessage(status: number, detail?: string): string {
    if (status === 401) return 'Email o contraseña incorrectos';
    if (status === 409) return 'El email ya está registrado';
    if (status === 422) return detail || 'Datos inválidos. Verificá los campos.';
    return detail || 'Ocurrió un error. Intentá de nuevo.';
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError('');
    try {
      const response = await api.post('/api/auth/login', { email, password });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      window.location.href = '/';
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      const status = apiErr.response?.status || 0;
      const detail = apiErr.response?.data?.detail;
      setError(getErrorMessage(status, detail));
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await api.post('/api/auth/register', { email, password });
      setSuccess('¡Cuenta creada con éxito! Redirigiendo al login...');
      setTimeout(() => {
        setIsRegistering(false);
        setSuccess('');
        setPassword('');
        setConfirmPassword('');
      }, 2000);
    } catch (err: unknown) {
      const apiErr = err as ApiError;
      const status = apiErr.response?.status || 0;
      const detail = apiErr.response?.data?.detail;
      setError(getErrorMessage(status, detail));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card" ref={formRef}>
          <div className="auth-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="40" height="40" rx="10" fill="#4f46e5" />
              <path d="M12 20l6 6 10-12" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 className="auth-title">ActiveTrace</h1>
          <p className="auth-subtitle">{isRegistering ? 'Creá tu cuenta' : 'Iniciá sesión'}</p>

          {error && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}

          <form onSubmit={isRegistering ? handleRegister : handleLogin} noValidate>
            <div className="auth-field">
              <label htmlFor="auth-email">Email</label>
              <input
                id="auth-email"
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setFieldErrors((prev) => ({ ...prev, email: undefined })); }}
                className={fieldErrors.email ? 'input-error' : ''}
              />
              {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
            </div>

            <div className="auth-field">
              <label htmlFor="auth-password">Contraseña</label>
              <input
                id="auth-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setFieldErrors((prev) => ({ ...prev, password: undefined })); }}
                className={fieldErrors.password ? 'input-error' : ''}
              />
              {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
            </div>

            {isRegistering && (
              <div className="auth-field">
                <label htmlFor="auth-confirm">Confirmar contraseña</label>
                <input
                  id="auth-confirm"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => { setConfirmPassword(e.target.value); setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined })); }}
                  className={fieldErrors.confirmPassword ? 'input-error' : ''}
                />
                {fieldErrors.confirmPassword && <span className="field-error">{fieldErrors.confirmPassword}</span>}
              </div>
            )}

            <button type="submit" className="btn btn-primary auth-btn" disabled={loading}>
              {loading ? (
                <span className="auth-spinner" />
              ) : isRegistering ? (
                'Crear cuenta'
              ) : (
                'Iniciar sesión'
              )}
            </button>
          </form>

          <p className="auth-toggle">
            {isRegistering ? (
              <>
                ¿Ya tenés cuenta?{' '}
                <button type="button" className="auth-link" onClick={() => setIsRegistering(false)}>
                  Iniciá sesión
                </button>
              </>
            ) : (
              <>
                ¿No tenés cuenta?{' '}
                <button type="button" className="auth-link" onClick={() => setIsRegistering(true)}>
                  Registrate
                </button>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
