import { computed, inject, Injectable, signal } from '@angular/core';
import { firstValueFrom, forkJoin } from 'rxjs';

import { IssueApiService } from '../../../core/issues/issue-api.service';
import { isApiError } from '../../../core/models/api-error.model';
import {
  CreateIssueRequest,
  EMPTY_FILTERS,
  Issue,
  IssueFilters,
  IssueSummary,
  UpdateIssueRequest,
} from '../../../core/models/issue.models';

interface IssueState {
  readonly issues: readonly Issue[];
  readonly summary: IssueSummary | null;
  readonly filters: IssueFilters;
  readonly loading: boolean;
  readonly error: string | null;
  /** Ids con una actualización en curso (deshabilita sus controles). */
  readonly pendingIds: ReadonlySet<string>;
}

const INITIAL_STATE: IssueState = {
  issues: [],
  summary: null,
  filters: EMPTY_FILTERS,
  loading: false,
  error: null,
  pendingIds: new Set(),
};

/**
 * Estado de la funcionalidad de incidencias (patrón *Store* con signals).
 * Se provee a nivel de ruta: vive mientras el usuario navega dentro de /issues.
 */
@Injectable()
export class IssueStore {
  private readonly api = inject(IssueApiService);
  private readonly state = signal<IssueState>(INITIAL_STATE);

  readonly issues = computed(() => this.state().issues);
  readonly summary = computed(() => this.state().summary);
  readonly filters = computed(() => this.state().filters);
  readonly loading = computed(() => this.state().loading);
  readonly error = computed(() => this.state().error);
  readonly hasActiveFilters = computed(() => {
    const f = this.state().filters;
    return f.status !== null || f.priority !== null;
  });

  isPending(id: string): boolean {
    return this.state().pendingIds.has(id);
  }

  /** Carga en paralelo el listado filtrado y el resumen global. */
  async load(): Promise<void> {
    this.patch({ loading: true, error: null });
    try {
      const { issues, summary } = await firstValueFrom(
        forkJoin({ issues: this.api.list(this.filters()), summary: this.api.summary() }),
      );
      this.patch({ issues, summary, loading: false });
    } catch (err) {
      this.patch({ loading: false, error: this.messageOf(err) });
    }
  }

  async setFilters(filters: IssueFilters): Promise<void> {
    const current = this.filters();
    if (current.status === filters.status && current.priority === filters.priority) return;
    this.patch({ filters });
    await this.load();
  }

  async create(payload: CreateIssueRequest): Promise<Issue> {
    const issue = await firstValueFrom(this.api.create(payload));
    // Se recarga para respetar filtros activos y actualizar el resumen.
    await this.load();
    return issue;
  }

  async update(id: string, changes: UpdateIssueRequest): Promise<void> {
    await this.mutate(id, async () => {
      const updated = await firstValueFrom(this.api.update(id, changes));
      this.replaceOrDrop(updated);
    });
  }

  /** Da por resuelta la incidencia (solo Administrador / Soporte). */
  async resolve(id: string): Promise<void> {
    await this.mutate(id, async () => {
      const resolved = await firstValueFrom(this.api.resolve(id));
      this.replaceOrDrop(resolved);
    });
  }

  /** Elimina la incidencia (solo Administrador / Soporte). */
  async remove(id: string): Promise<void> {
    await this.mutate(id, async () => {
      await firstValueFrom(this.api.remove(id));
      this.patch({ issues: this.issues().filter((i) => i.id !== id) });
    });
  }

  /**
   * Plantilla común de las operaciones sobre una incidencia: marca el estado
   * pendiente, ejecuta la operación, refresca el resumen y gestiona el error.
   */
  private async mutate(id: string, operation: () => Promise<void>): Promise<void> {
    this.setPending(id, true);
    this.patch({ error: null });
    try {
      await operation();
      this.patch({ summary: await firstValueFrom(this.api.summary()) });
    } catch (err) {
      this.patch({ error: this.messageOf(err) });
    } finally {
      this.setPending(id, false);
    }
  }

  /** Reemplaza la incidencia o la retira si ya no cumple los filtros activos. */
  private replaceOrDrop(updated: Issue): void {
    const { status, priority } = this.filters();
    const stillMatches =
      (status === null || updated.status === status) &&
      (priority === null || updated.priority === priority);
    const issues = stillMatches
      ? this.issues().map((i) => (i.id === updated.id ? updated : i))
      : this.issues().filter((i) => i.id !== updated.id);
    this.patch({ issues });
  }

  clearError(): void {
    this.patch({ error: null });
  }

  private setPending(id: string, pending: boolean): void {
    const next = new Set(this.state().pendingIds);
    if (pending) next.add(id);
    else next.delete(id);
    this.patch({ pendingIds: next });
  }

  private patch(partial: Partial<IssueState>): void {
    this.state.update((s) => ({ ...s, ...partial }));
  }

  private messageOf(err: unknown): string {
    return isApiError(err) ? err.message : 'Ocurrió un error inesperado. Intente más tarde.';
  }
}
