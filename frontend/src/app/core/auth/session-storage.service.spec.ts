import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { adminUser } from '../../testing/test-data';
import { Session } from '../models/auth.models';
import { SessionStorageService } from './session-storage.service';

describe('SessionStorageService', () => {
  let service: SessionStorageService;
  const session: Session = { token: 't', expiresAt: Date.now() + 1000, user: adminUser };

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({ providers: [provideZonelessChangeDetection()] });
    service = TestBed.inject(SessionStorageService);
  });

  it('guarda y lee la sesión', () => {
    service.write(session);
    expect(service.read()).toEqual(session);
  });

  it('devuelve null si no hay sesión', () => {
    expect(service.read()).toBeNull();
  });

  it('descarta datos corruptos', () => {
    sessionStorage.setItem('issue-tracker.session', '{no-json');
    expect(service.read()).toBeNull();
  });

  it('descarta objetos con forma inválida', () => {
    sessionStorage.setItem('issue-tracker.session', JSON.stringify({ token: 1 }));
    expect(service.read()).toBeNull();
  });

  it('limpia la sesión', () => {
    service.write(session);
    service.clear();
    expect(service.read()).toBeNull();
  });
});
