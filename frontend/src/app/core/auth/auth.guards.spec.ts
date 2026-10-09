import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { authGuard, guestGuard, permissionGuard } from './auth.guards';
import { AuthService } from './auth.service';

describe('Guards de autenticación', () => {
  let authenticated: boolean;
  const route = {} as ActivatedRouteSnapshot;
  const state = { url: '/issues/new' } as RouterStateSnapshot;

  beforeEach(() => {
    authenticated = false;
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideRouter([]),
        {
          provide: AuthService,
          useValue: { isAuthenticated: () => authenticated, can: () => authenticated },
        },
      ],
    });
  });

  const run = (guard: typeof authGuard) =>
    TestBed.runInInjectionContext(() => guard(route, state));

  it('authGuard permite el acceso con sesión', () => {
    authenticated = true;
    expect(run(authGuard)).toBeTrue();
  });

  it('authGuard redirige al login conservando la URL solicitada', () => {
    const result = run(authGuard) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(result)).toBe(
      '/login?returnUrl=%2Fissues%2Fnew',
    );
  });

  it('guestGuard envía al listado si ya hay sesión', () => {
    authenticated = true;
    const result = run(guestGuard) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(result)).toBe('/issues');
  });

  it('guestGuard permite ver el login sin sesión', () => {
    expect(run(guestGuard)).toBeTrue();
  });

  it('permissionGuard permite el acceso con el permiso', () => {
    authenticated = true;
    expect(run(permissionGuard('stats:view'))).toBeTrue();
  });

  it('permissionGuard envía al listado si falta el permiso', () => {
    const result = run(permissionGuard('stats:view')) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(result)).toBe('/issues');
  });
});
