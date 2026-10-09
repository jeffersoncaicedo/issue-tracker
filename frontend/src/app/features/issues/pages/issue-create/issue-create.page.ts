import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isApiError } from '../../../../core/models/api-error.model';
import { ISSUE_PRIORITIES, IssuePriority } from '../../../../core/models/issue.models';
import { PRIORITY_LABELS } from '../../../../shared/labels/issue-labels';
import { PriorityMeter } from '../../../../shared/priority-meter/priority-meter';
import { IssueStore } from '../../data/issue.store';

export const TITLE_MIN = 3;
export const TITLE_MAX = 120;
export const DESCRIPTION_MAX = 2000;

/** Alta de incidencias con validación alineada a las reglas del API. */
@Component({
  selector: 'app-issue-create-page',
  imports: [ReactiveFormsModule, RouterLink, PriorityMeter],
  templateUrl: './issue-create.page.html',
  styleUrl: './issue-create.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IssueCreatePage {
  private readonly store = inject(IssueStore);
  private readonly router = inject(Router);

  protected readonly priorities = ISSUE_PRIORITIES;
  protected readonly priorityLabels = PRIORITY_LABELS;
  protected readonly limits = { TITLE_MIN, TITLE_MAX, DESCRIPTION_MAX };

  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly form = inject(NonNullableFormBuilder).group({
    title: [
      '',
      [Validators.required, Validators.minLength(TITLE_MIN), Validators.maxLength(TITLE_MAX)],
    ],
    description: ['', [Validators.maxLength(DESCRIPTION_MAX)]],
    priority: ['medium' as IssuePriority, [Validators.required]],
  });

  protected async submit(): Promise<void> {
    const title = this.form.controls.title;
    title.setValue(title.value.trim());
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.errorMessage.set(null);
    try {
      await this.store.create(this.form.getRawValue());
      await this.router.navigate(['/issues']);
    } catch (err) {
      this.errorMessage.set(
        isApiError(err) ? err.message : 'No se pudo registrar la incidencia. Intente de nuevo.',
      );
      this.submitting.set(false);
    }
  }

  protected showError(name: 'title' | 'description'): boolean {
    const c = this.form.controls[name];
    return c.invalid && (c.touched || c.dirty);
  }

  protected titleError(): string {
    const c = this.form.controls.title;
    if (c.hasError('required')) return 'Escriba un título para la incidencia.';
    if (c.hasError('minlength')) return `El título debe tener al menos ${TITLE_MIN} caracteres.`;
    return `El título no puede superar ${TITLE_MAX} caracteres.`;
  }
}
