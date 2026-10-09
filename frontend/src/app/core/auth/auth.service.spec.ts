import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { API, regularUser, tokenResponse } from '../../testing/test-data';
import { API_BASE_URL } from '../config/api.config';
import { AuthService } from './auth.service';
import { SessionStorageService } from './session-storage.service';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;
  let router: Router;

  function setup(): void {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: API_BASE_URL, useValue: API },
      ],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
  }

  beforeEach(() => sessionStorage.clear());
  afterEach(() => http.verify());

  it('inicia sin sesión', () => {
    setup();
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.user()).toBeNull();
  });

  it('login guarda la sesión y expone el usuario', () => {
    setup();
    let username = '';
    service.login({ username: 'admin', password: 'x' }).subscribe((u) => (username = u.username));

    const req = http.expectOne(`${API}/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ username: 'admin', password: 'x' });
    req.flush(tokenResponse);

    expect(username).toBe('admin');
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.token()).toBe('jwt-token');
    expect(TestBed.inject(SessionStorageService).read()?.token).toBe('jwt-token');
  });

  it('considera expirada una sesión vencida y la limpia', () => {
    sessionStorage.setItem(
      'issue-tracker.session',
      JSON.stringify({ token: 't', expiresAt: Date.now() - 1, user: tokenResponse.user }),
    );
    setup();
    expect(service.isAuthenticated()).toBeFalse();
    expect(sessionStorage.getItem('issue-tracker.session')).toBeNull();
  });

  it('logout revoca el token, limpia la sesión y redirige al login', () => {
    setup();
    service.login({ username: 'admin', password: 'x' }).subscribe();
    http.expectOne(`${API}/auth/login`).flush(tokenResponse);

    service.logout().subscribe();
    http.expectOne(`${API}/auth/logout`).flush(null, { status: 204, statusText: 'No Content' });

    expect(service.isAuthenticated()).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('logout cierra la sesión local aunque el servidor falle', () => {
    setup();
    service.login({ username: 'admin', password: 'x' }).subscribe();
    http.expectOne(`${API}/auth/login`).flush(tokenResponse);

    service.logout().subscribe();
    http.expectOne(`${API}/auth/logout`).error(new ProgressEvent('error'));

    expect(service.isAuthenticated()).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('logout sin sesión solo redirige', () => {
    setup();
    service.logout().subscribe();
    http.expectNone(`${API}/auth/logout`);
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('can() refleja los permisos del usuario autenticado', () => {
    setup();
    expect(service.can('issues:delete')).toBeFalse();
    service.login({ username: 'admin', password: 'x' }).subscribe();
    http.expectOne(`${API}/auth/login`).flush(tokenResponse);
    expect(service.can('issues:delete')).toBeTrue();
    expect(service.can('stats:view')).toBeTrue();
  });

  it('can() es falso para un usuario sin permisos', () => {
    setup();
    service.login({ username: 'analista', password: 'x' }).subscribe();
    http.expectOne(`${API}/auth/login`).flush({ ...tokenResponse, user: regularUser });
    expect(service.can('issues:resolve')).toBeFalse();
  });
});
