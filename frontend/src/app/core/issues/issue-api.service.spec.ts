import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { aSummary, anIssue, API } from '../../testing/test-data';
import { API_BASE_URL } from '../config/api.config';
import { EMPTY_FILTERS } from '../models/issue.models';
import { IssueApiService } from './issue-api.service';

describe('IssueApiService', () => {
  let service: IssueApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: API },
      ],
    });
    service = TestBed.inject(IssueApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista sin parámetros cuando no hay filtros', () => {
    service.list(EMPTY_FILTERS).subscribe();
    const req = http.expectOne(`${API}/issues`);
    expect(req.request.params.keys()).toEqual([]);
    req.flush([anIssue()]);
  });

  it('envía los filtros como query params', () => {
    service.list({ status: 'completed', priority: 'low' }).subscribe();
    const req = http.expectOne((r) => r.url === `${API}/issues`);
    expect(req.request.params.get('status')).toBe('completed');
    expect(req.request.params.get('priority')).toBe('low');
    req.flush([]);
  });

  it('obtiene el resumen', () => {
    service.summary().subscribe((s) => expect(s).toEqual(aSummary));
    http.expectOne(`${API}/issues/summary`).flush(aSummary);
  });

  it('crea con POST', () => {
    const payload = { title: 'T', description: '', priority: 'low' as const };
    service.create(payload).subscribe();
    const req = http.expectOne(`${API}/issues`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(anIssue());
  });

  it('actualiza con PATCH y codifica el id', () => {
    service.update('a/b', { status: 'completed' }).subscribe();
    const req = http.expectOne(`${API}/issues/a%2Fb`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ status: 'completed' });
    req.flush(anIssue());
  });

  it('resuelve con POST /resolve', () => {
    service.resolve('i1').subscribe();
    const req = http.expectOne(`${API}/issues/i1/resolve`);
    expect(req.request.method).toBe('POST');
    req.flush(anIssue({ status: 'completed' }));
  });

  it('elimina con DELETE', () => {
    service.remove('i1').subscribe();
    const req = http.expectOne(`${API}/issues/i1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });

  it('obtiene las estadísticas', () => {
    service.stats().subscribe();
    http.expectOne(`${API}/issues/stats`).flush({});
  });
});
