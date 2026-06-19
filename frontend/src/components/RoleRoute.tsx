import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { getCurrentUser, type User } from '../services/api';

interface RoleRouteProps {
  roles: string[];
}

export default function RoleRoute({ roles }: RoleRouteProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Verificando permisos...</div>;

  if (!user) return <Navigate to="/login" replace />;

  const hasRole = roles.length === 0 || roles.some((r) => user.roles.includes(r));

  if (!hasRole) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
