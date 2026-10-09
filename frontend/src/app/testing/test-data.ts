import { TokenResponse, User } from '../core/models/auth.models';
import { Issue, IssueSummary } from '../core/models/issue.models';

/** Datos de prueba reutilizables (patrón *Object Mother*). */
export const API = 'http://api.test/api/v1';

export const adminUser: User = {
  id: 'u1',
  username: 'admin',
  full_name: 'Administrador',
  role: 'admin',
  permissions: ['issues:delete', 'issues:resolve', 'stats:view'],
};

export const regularUser: User = {
  id: 'u3',
  username: 'analista',
  full_name: 'Ana Analista',
  role: 'user',
  permissions: [],
};

export const tokenResponse: TokenResponse = {
  access_token: 'jwt-token',
  token_type: 'bearer',
  expires_in: 3600,
  user: adminUser,
};

export function anIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: 'i1',
    title: 'Falla en reporte',
    description: 'Detalle',
    priority: 'high',
    status: 'open',
    created_by: 'admin',
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
    ...overrides,
  };
}

export const aSummary: IssueSummary = { total: 4, open: 2, in_progress: 1, completed: 1 };
