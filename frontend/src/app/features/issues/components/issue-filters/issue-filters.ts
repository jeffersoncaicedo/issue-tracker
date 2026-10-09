import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  effect,
  inject,
  input,
  output,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';

import {
  ISSUE_PRIORITIES,
  ISSUE_STATUSES,
  IssueFilters,
  IssuePriority,
  IssueStatus,
} from '../../../../core/models/issue.models';
import { PRIORITY_LABELS, STATUS_LABELS } from '../../../../shared/labels/issue-labels';

type FiltersForm = FormGroup<{
  status: FormControl<IssueStatus | null>;
  priority: FormControl<IssuePriority | null>;
}>;

/** Filtros por estado y prioridad (Reactive Form tipado, sincronizado con el store). */
@Component({
  selector: 'app-issue-filters',
  imports: [ReactiveFormsModule],
  templateUrl: './issue-filters.html',
  styleUrl: './issue-filters.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IssueFiltersBar {
  readonly filters = input.required<IssueFilters>();
  readonly filtersChange = output<IssueFilters>();

  protected readonly statuses = ISSUE_STATUSES;
  protected readonly priorities = ISSUE_PRIORITIES;
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly priorityLabels = PRIORITY_LABELS;

  protected readonly hasFilters = computed(
    () => this.filters().status !== null || this.filters().priority !== null,
  );

  protected readonly form: FiltersForm = new FormGroup({
    status: new FormControl<IssueStatus | null>(null),
    priority: new FormControl<IssuePriority | null>(null),
  });

  constructor() {
    // Estado externo → formulario (p. ej. al filtrar desde el resumen) sin re-emitir.
    effect(() => this.form.setValue(this.filters(), { emitEvent: false }));

    this.form.valueChanges
      .pipe(takeUntilDestroyed(inject(DestroyRef)))
      .subscribe(() => this.filtersChange.emit(this.form.getRawValue()));
  }

  protected clear(): void {
    this.form.setValue({ status: null, priority: null });
  }

}
