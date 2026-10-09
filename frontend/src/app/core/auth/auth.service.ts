import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, EMPTY, finalize, map, Observable, tap } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import { LoginRequest, Permission, Session, TokenResponse, User } from '../models/auth.models';
import { SessionStorageService } from './session-storage.service';

/**
 * Fuente única de verdad del estado de autenticación (signals).
 * Los componentes leen `user()` / `isAuthenticated()`; nunca acceden al storage.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly storage = inject(SessionStorageService);
  private readonly baseUrl = inject(API_BASE_URL);

  private readonly session = signal<Session | null>(this.storage.read());

  readonly user = computed<User | null>(() => this.session()?.user ?? null);

  /**
   * Indica si el usuario tiene un permiso. Solo controla qué ve la interfaz:
   * la autorización real la aplica el backend en cada petición.
   */
  can(permission: Permission): boolean {
    return this.user()?.permissions?.includes(permission) ?? false;
  }

  /** Evaluado en cada lectura para considerar la expiración del token. */
  isAuthenticated(): boolean {
    const current = this.session();
    if (!current) return false;
    if (current.expiresAt <= Date.now()) {
      this.clearSession();
      return false;
    }
    return true;
  }

  token(): string | null {
    return this.isAuthenticated() ? (this.session()?.token ?? null) : null;
  }

  login(credentials: LoginRequest): Observable<User> {
    return this.http.post<TokenResponse>(`${this.baseUrl}/auth/login`, credentials).pipe(
      map((res) => ({
        token: res.access_token,
        expiresAt: Date.now() + res.expires_in * 1000,
        user: res.user,
      })),
      tap((session) => {
        this.storage.write(session);
        this.session.set(session);
      }),
      map((session) => session.user),
    );
  }

  /**
   * Revoca el token en el servidor y limpia la sesión local. Aunque la llamada
   * falle (red caída, token ya expirado), el usuario siempre sale de la app.
   */
  logout(): Observable<void> {
    if (!this.token()) {
      this.finishLogout();
      return EMPTY;
    }
    return this.http.post<void>(`${this.baseUrl}/auth/logout`, {}).pipe(
      catchError(() => EMPTY),
      finalize(() => this.finishLogout()),
    );
  }

  /** Limpia la sesión sin llamar al servidor (p. ej. ante un 401). */
  clearSession(): void {
    this.storage.clear();
    this.session.set(null);
  }

  private finishLogout(): void {
    this.clearSession();
    void this.router.navigate(['/login']);
  }
}
