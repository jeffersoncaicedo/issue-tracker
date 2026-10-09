import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { IssuePriority } from '../../core/models/issue.models';
import { PRIORITY_LABELS, PRIORITY_LEVEL } from '../labels/issue-labels';

/** Indicador de prioridad tipo "barras de señal": 3 = alta, 1 = baja. */
@Component({
  selector: 'app-priority-meter',
  template: `
    <span class="meter" [attr.data-level]="level()" role="img" [attr.aria-label]="'Prioridad ' + label()">
      <span class="meter__bar"></span><span class="meter__bar"></span><span class="meter__bar"></span>
    </span>
  `,
  styles: `
    .meter { display: inline-flex; align-items: flex-end; gap: 2px; height: 0.875rem; }
    .meter__bar { width: 4px; border-radius: 1px; background: var(--line); }
    .meter__bar:nth-child(1) { height: 40%; }
    .meter__bar:nth-child(2) { height: 70%; }
    .meter__bar:nth-child(3) { height: 100%; }
    [data-level='1'] .meter__bar:nth-child(-n + 1) { background: var(--priority-low); }
    [data-level='2'] .meter__bar:nth-child(-n + 2) { background: var(--priority-medium); }
    [data-level='3'] .meter__bar:nth-child(-n + 3) { background: var(--priority-high); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PriorityMeter {
  readonly priority = input.required<IssuePriority>();
  protected readonly level = computed(() => PRIORITY_LEVEL[this.priority()]);
  protected readonly label = computed(() => PRIORITY_LABELS[this.priority()].toLowerCase());
}
