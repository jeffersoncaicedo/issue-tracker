import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, OnInit, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/auth/auth.service';

import {
  EMPTY_FILTERS,
  ISSUE_PRIORITIES,
  ISSUE_STATUSES,
  Issue,
  IssueFilters,
  IssuePriority,
  IssueStatus,
} from '../../../../core/models/issue.models';
import { PRIORITY_LABELS, STATUS_LABELS } from '../../../../shared/labels/issue-labels';
import { ConfirmDialog } from '../../../../shared/confirm-dialog/confirm-dialog';
import { PriorityMeter } from '../../../../shared/priority-meter/priority-meter';
import { IssueFiltersBar } from '../../components/issue-filters/issue-filters';
import { SummaryBar } from '../../components/summary-bar/summary-bar';
import { IssueStore } from '../../data/issue.store';

/** Página principal: resumen, filtros y listado editable de incidencias. */
@Component({
  selector: 'app-issue-list-page',
  imports: [RouterLink, DatePipe, SummaryBar, IssueFiltersBar, PriorityMeter, ConfirmDialog],
  templateUrl: './issue-list.page.html',
  styleUrl: './issue-list.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IssueListPage implements OnInit {
  protected readonly store = inject(IssueStore);
  private readonly auth = inject(AuthService);
  private readonly confirmDialog = viewChild.required(ConfirmDialog);

  /** Permisos de la sesión (la autorización definitiva la aplica el API). */
  protected readonly canResolve = this.auth.can('issues:resolve');
  protected readonly canDelete = this.auth.can('issues:delete');

  protected readonly statuses = ISSUE_STATUSES;
  protected readonly priorities = ISSUE_PRIORITIES;
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly priorityLabels = PRIORITY_LABELS;

  ngOnInit(): void {
    void this.store.load();
  }

  protected onFiltersChange(filters: IssueFilters): void {
    void this.store.setFilters(filters);
  }

  protected onStatusToggled(status: IssueStatus | null): void {
    void this.store.setFilters({ ...this.store.filters(), status });
  }

  protected clearFilters(): void {
    void this.store.setFilters(EMPTY_FILTERS);
  }

  protected changeStatus(issue: Issue, event: Event): void {
    const status = (event.target as HTMLSelectElement).value as IssueStatus;
    if (status !== issue.status) void this.store.update(issue.id, { status });
  }

  protected changePriority(issue: Issue, event: Event): void {
    const priority = (event.target as HTMLSelectElement).value as IssuePriority;
    if (priority !== issue.priority) void this.store.update(issue.id, { priority });
  }

  /** Un usuario sin permiso de resolución no puede editar incidencias completadas. */
  protected isLocked(issue: Issue): boolean {
    return issue.status === 'completed' && !this.canResolve;
  }

  /** La opción "Completado" solo está disponible para quien puede resolver. */
  protected isStatusOptionDisabled(status: IssueStatus, issue: Issue): boolean {
    return status === 'completed' && !this.canResolve && issue.status !== 'completed';
  }

  protected resolve(issue: Issue): void {
    void this.store.resolve(issue.id);
  }

  protected async remove(issue: Issue): Promise<void> {
    const confirmed = await this.confirmDialog().open({
      title: 'Eliminar incidencia',
      message: `Se eliminará "${issue.title}" de forma permanente. Esta acción no se puede deshacer.`,
      confirmLabel: 'Eliminar',
      tone: 'danger',
    });
    if (confirmed) await this.store.remove(issue.id);
  }
}
