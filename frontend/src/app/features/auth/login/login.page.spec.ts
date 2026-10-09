import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthService } from '../../../core/auth/auth.service';
import { tokenResponse } from '../../../testing/test-data';
import { LoginPage } from './login.page';

describe('LoginPage', () => {
  let fixture: ComponentFixture<LoginPage>;
  let auth: jasmine.SpyObj<AuthService>;
  let router: Router;
  let el: HTMLElement;

  beforeEach(async () => {
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['login']);
    await TestBed.configureTestingModule({
      imports: [LoginPage],
      providers: [
        provideZonelessChangeDetection(),
        provideRouter([]),
        { provide: AuthService, useValue: auth },
      ],
    }).compileComponents();
    router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
    fixture = TestBed.createComponent(LoginPage);
    el = fixture.nativeElement;
    await fixture.whenStable();
  });

  function fill(username: string, password: string): void {
    for (const [id, value] of [['username', username], ['password', password]]) {
      const input = el.querySelector<HTMLInputElement>(`#${id}`)!;
      input.value = value;
      input.dispatchEvent(new Event('input'));
    }
  }

  async function submit(): Promise<void> {
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  }

  it('valida campos obligatorios sin llamar al API', async () => {
    await submit();
    expect(auth.login).not.toHaveBeenCalled();
    expect(el.querySelector('#username-error')?.textContent).toContain('Ingrese su usuario');
    expect(el.querySelector('#password-error')).not.toBeNull();
  });

  it('inicia sesión y navega al listado', async () => {
    auth.login.and.returnValue(of(tokenResponse.user));
    fill('admin', 'Admin#2026');
    await submit();
    expect(auth.login).toHaveBeenCalledWith({ username: 'admin', password: 'Admin#2026' });
    expect(router.navigateByUrl).toHaveBeenCalledWith('/issues');
  });

  it('respeta returnUrl interno', async () => {
    fixture.componentRef.setInput('returnUrl', '/issues/new');
    auth.login.and.returnValue(of(tokenResponse.user));
    fill('admin', 'x');
    await submit();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/issues/new');
  });

  it('ignora returnUrl externo (evita open redirect)', async () => {
    fixture.componentRef.setInput('returnUrl', '//evil.com');
    auth.login.and.returnValue(of(tokenResponse.user));
    fill('admin', 'x');
    await submit();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/issues');
  });

  it('muestra el mensaje de credenciales inválidas y limpia la contraseña', async () => {
    auth.login.and.returnValue(
      throwError(() => ({ status: 401, code: 'invalid_credentials', message: 'Usuario o contraseña incorrectos.' })),
    );
    fill('admin', 'mala');
    await submit();
    expect(el.querySelector('[role=alert]')?.textContent).toContain('incorrectos');
    expect(el.querySelector<HTMLInputElement>('#password')!.value).toBe('');
  });

  it('avisa cuando la sesión expiró', async () => {
    fixture.componentRef.setInput('reason', 'expired');
    await fixture.whenStable();
    expect(el.querySelector('[role=status]')?.textContent).toContain('Su sesión terminó');
  });
});
