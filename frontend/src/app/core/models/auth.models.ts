export type Role = 'admin' | 'support' | 'user';

/** Capacidades que otorga el backend según el rol (RBAC). */
export type Permission = 'issues:resolve' | 'issues:delete' | 'stats:view';

export const ROLE_LABELS: Readonly<Record<Role, string>> = {
  admin: 'Administrador',
  support: 'Soporte',
  user: 'Usuario',
};

export interface User {
  readonly id: string;
  readonly username: string;
  readonly full_name: string;
  readonly role: Role;
  readonly permissions: readonly Permission[];
}

export interface LoginRequest {
  readonly username: string;
  readonly password: string;
}

export interface TokenResponse {
  readonly access_token: string;
  readonly token_type: 'bearer';
  /** Vigencia en segundos. */
  readonly expires_in: number;
  readonly user: User;
}

/** Sesión persistida en el navegador. */
export interface Session {
  readonly token: string;
  /** Epoch en milisegundos. */
  readonly expiresAt: number;
  readonly user: User;
}
