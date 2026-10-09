import { ChangeDetectionStrategy, Component, computed, inject, OnInit, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { IssueApiService } from '../../core/issues/issue-api.service';
import { isApiError } from '../../core/models/api-error.model';
import {
  ISSUE_PRIORITIES,
  ISSUE_STATUSES,
  IssueStats,
} from '../../core/models/issue.models';
import { PRIORITY_LABELS, STATUS_LABELS } from '../../shared/labels/issue-labels';
import {
  buildDonut,
  buildPareto,
  buildPriorityRows,
  PARETO_BOX,
  percentOf,
} from './chart-geometry';

export const DONUT_RADIUS = 70;

/**
 * Vista de resumen (Administrador / Soporte): distribución por estado,
 * diagrama de Pareto y carga por prioridad.
 */
@Component({
  selector: 'app-dashboard-page',
  templateUrl: './dashboard.page.html',
  styleUrl: './dashboard.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPage implements OnInit {
  private readonly api = inject(IssueApiService);

  protected readonly stats = signal<IssueStats | null>(null);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly statuses = ISSUE_STATUSES;
  protected readonly priorities = ISSUE_PRIORITIES;
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly priorityLabels = PRIORITY_LABELS;
  protected readonly radius = DONUT_RADIUS;
  protected readonly box = PARETO_BOX;
  protected readonly percentOf = percentOf;

  protected readonly donut = computed(() => {
    const s = this.stats();
    return s ? buildDonut(s.by_status, DONUT_RADIUS) : [];
  });

  protected readonly pareto = computed(() => {
    const s = this.stats();
    return s ? buildPareto(s.by_status) : null;
  });

  protected readonly priorityRows = computed(() => {
    const s = this.stats();
    return s ? buildPriorityRows(s.matrix) : [];
  });

  /** Incidencias aún sin resolver (abiertas + en progreso). */
  protected readonly pending = computed(() => {
    const s = this.stats();
    return s ? s.by_status.open + s.by_status.in_progress : 0;
  });

  protected readonly pendingHigh = computed(() => {
    const s = this.stats();
    return s ? s.matrix.open.high + s.matrix.in_progress.high : 0;
  });

  ngOnInit(): void {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      this.stats.set(await firstValueFrom(this.api.stats()));
    } catch (err) {
      this.error.set(
        isApiError(err) ? err.message : 'No se pudo cargar el resumen. Intente más tarde.',
      );
    } finally {
      this.loading.set(false);
    }
  }
}
