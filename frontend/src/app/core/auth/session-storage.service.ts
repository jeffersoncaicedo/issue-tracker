import { Injectable } from '@angular/core';

import { Session } from '../models/auth.models';

const STORAGE_KEY = 'issue-tracker.session';

/**
 * Persiste la sesión en `sessionStorage`: se elimina al cerrar la pestaña,
 * lo que reduce la ventana de exposición del token frente a `localStorage`.
 */
@Injectable({ providedIn: 'root' })
export class SessionStorageService {
  read(): Session | null {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as Partial<Session>;
      return this.isValidShape(parsed) ? parsed : null;
    } catch {
      // Datos corruptos o almacenamiento no disponible: se ignora la sesión.
      this.clear();
      return null;
    }
  }

  write(session: Session): void {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }

  clear(): void {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* almacenamiento no disponible: nada que limpiar */
    }
  }

  private isValidShape(value: Partial<Session>): value is Session {
    return (
      typeof value.token === 'string' &&
      typeof value.expiresAt === 'number' &&
      typeof value.user?.username === 'string'
    );
  }
}
