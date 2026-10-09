import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import {
  CreateIssueRequest,
  Issue,
  IssueFilters,
  IssueStats,
  IssueSummary,
  UpdateIssueRequest,
} from '../models/issue.models';

/** Cliente HTTP del recurso `/issues` (sin estado; patrón Gateway). */
@Injectable({ providedIn: 'root' })
export class IssueApiService {
  private readonly http = inject(HttpClient);
  private readonly url = `${inject(API_BASE_URL)}/issues`;

  list(filters: IssueFilters): Observable<Issue[]> {
    let params = new HttpParams();
    if (filters.status) params = params.set('status', filters.status);
    if (filters.priority) params = params.set('priority', filters.priority);
    return this.http.get<Issue[]>(this.url, { params });
  }

  summary(): Observable<IssueSummary> {
    return this.http.get<IssueSummary>(`${this.url}/summary`);
  }

  create(payload: CreateIssueRequest): Observable<Issue> {
    return this.http.post<Issue>(this.url, payload);
  }

  update(id: string, changes: UpdateIssueRequest): Observable<Issue> {
    return this.http.patch<Issue>(this.itemUrl(id), changes);
  }

  /** Da la incidencia por resuelta (requiere permiso `issues:resolve`). */
  resolve(id: string): Observable<Issue> {
    return this.http.post<Issue>(`${this.itemUrl(id)}/resolve`, {});
  }

  /** Elimina la incidencia (requiere permiso `issues:delete`). */
  remove(id: string): Observable<void> {
    return this.http.delete<void>(this.itemUrl(id));
  }

  /** Estadísticas por estado y prioridad (requiere permiso `stats:view`). */
  stats(): Observable<IssueStats> {
    return this.http.get<IssueStats>(`${this.url}/stats`);
  }

  private itemUrl(id: string): string {
    return `${this.url}/${encodeURIComponent(id)}`;
  }
}
