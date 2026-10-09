import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { ISSUE_STATUSES, IssueStatus, IssueSummary } from '../../../../core/models/issue.models';
import { STATUS_LABELS } from '../../../../shared/labels/issue-labels';

export interface SummarySegment {
  readonly status: IssueStatus;
  readonly label: string;
  readonly count: number;
  /** Porcentaje entero sobre el total (0 si no hay incidencias). */
  readonly percent: number;
}

/**
 * Resumen por estado: una barra proporcional + leyenda con totales.
 * Cada estado es un botón que activa/desactiva el filtro correspondiente.
 */
@Component({
  selector: 'app-summary-bar',
  templateUrl: './summary-bar.html',
  styleUrl: './summary-bar.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SummaryBar {
  readonly summary = input.required<IssueSummary>();
  readonly activeStatus = input<IssueStatus | null>(null);
  readonly statusToggled = output<IssueStatus | null>();

  protected readonly segments = computed<SummarySegment[]>(() => {
    const s = this.summary();
    return ISSUE_STATUSES.map((status) => ({
      status,
      label: STATUS_LABELS[status],
      count: s[status],
      percent: s.total ? Math.round((s[status] / s.total) * 100) : 0,
    }));
  });

  protected toggle(status: IssueStatus): void {
    this.statusToggled.emit(this.activeStatus() === status ? null : status);
  }
}
