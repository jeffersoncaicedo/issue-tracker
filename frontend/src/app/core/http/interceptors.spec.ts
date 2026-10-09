import { HttpClient, HttpErrorResponse, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { API } from '../../testing/test-data';
import { AuthService } from '../auth/auth.service';
import { API_BASE_URL } from '../config/api.config';
import { ApiError } from '../models/api-error.model';
import { authInterceptor } from './auth.interceptor';
import { errorInterceptor, toApiError } from './error.interceptor';

describe('Interceptores HTTP', () => {
  let http: HttpClient;
  let backend: HttpTestingController;
  let token: string | null;
  let clearSession: jasmine.Spy;
  let router: Router;

  beforeEach(() => {
    token = 'abc';
    clearSession = jasmine.createSpy('clearSession');
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
        { provide: AuthService, useValue: { token: () => token, clearSession } },
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
  });

  afterEach(() => backend.verify());

  describe('authInterceptor', () => {
    it('agrega el Bearer token a las peticiones del API', () => {
      http.get(`${API}/issues`).subscribe();
      const req = backend.expectOne(`${API}/issues`);
      expect(req.request.headers.get('Authorization')).toBe('Bearer abc');
      req.flush([]);
    });

    it('NO envía el token a dominios externos', () => {
      http.get('https://otro-dominio.com/data').subscribe();
      const req = backend.expectOne('https://otro-dominio.com/data');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('no agrega cabecera si no hay sesión', () => {
      token = null;
      http.get(`${API}/issues`).subscribe();
      const req = backend.expectOne(`${API}/issues`);
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush([]);
    });
  });

  describe('errorInterceptor', () => {
    it('normaliza el error del backend', () => {
      let error: ApiError | undefined;
      http.get(`${API}/issues/x`).subscribe({ error: (e: ApiError) => (error = e) });
      backend
        .expectOne(`${API}/issues/x`)
        .flush({ error: { code: 'not_found', message: 'No existe' } }, { status: 404, statusText: 'NF' });
      expect(error).toEqual({ status: 404, code: 'not_found', message: 'No existe' });
    });

    it('ante un 401 limpia la sesión y redirige al login', () => {
      http.get(`${API}/issues`).subscribe({ error: () => undefined });
      backend.expectOne(`${API}/issues`).flush({}, { status: 401, statusText: 'Unauthorized' });
      expect(clearSession).toHaveBeenCalled();
      expect(router.navigate).toHaveBeenCalledWith(['/login'], { queryParams: { reason: 'expired' } });
    });

    it('un 401 del login NO redirige (son credenciales inválidas)', () => {
      http.post(`${API}/auth/login`, {}).subscribe({ error: () => undefined });
      backend.expectOne(`${API}/auth/login`).flush({}, { status: 401, statusText: 'Unauthorized' });
      expect(clearSession).not.toHaveBeenCalled();
      expect(router.navigate).not.toHaveBeenCalled();
    });
  });

  describe('toApiError', () => {
    it('usa un mensaje claro cuando no hay conexión', () => {
      const e = toApiError(new HttpErrorResponse({ status: 0 }));
      expect(e.code).toBe('network_error');
      expect(e.message).toContain('No se pudo conectar');
    });

    it('usa un mensaje genérico para estados desconocidos', () => {
      const e = toApiError(new HttpErrorResponse({ status: 418 }));
      expect(e.message).toContain('error inesperado');
    });
  });
});
