import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { IssueApiService } from '../../core/issues/issue-api.service';
import { IssueStats } from '../../core/models/issue.models';
import { DashboardPage } from './dashboard.page';

const STATS: IssueStats = {
  total: 6,
  by_status: { open: 3, in_progress: 1, completed: 2 },
  by_priority: { high: 3, medium: 2, low: 1 },
  matrix: {
    open: { high: 2, medium: 1, low: 0 },
    in_progress: { high: 0, medium: 1, low: 0 },
    completed: { high: 1, medium: 0, low: 1 },
  },
};

describe('DashboardPage', () => {
  let fixture: ComponentFixture<DashboardPage>;
  let api: jasmine.SpyObj<IssueApiService>;
  let el: HTMLElement;

  async function create(): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [DashboardPage],
      providers: [provideZonelessChangeDetection(), { provide: IssueApiService, useValue: api }],
    }).compileComponents();
    fixture = TestBed.createComponent(DashboardPage);
    el = fixture.nativeElement;
    await fixture.whenStable();
  }

  beforeEach(() => {
    api = jasmine.createSpyObj<IssueApiService>('IssueApiService', ['stats']);
  });

  it('muestra el total, el anillo y la frase de pendientes', async () => {
    api.stats.and.returnValue(of(STATS));
    await create();
    expect(el.querySelector('.donut__total')?.textContent).toBe('6');
    expect(el.querySelectorAll('.donut__seg').length).toBe(3);
    expect(el.querySelector('.head__lead')?.textContent).toContain('4 sin resolver');
    expect(el.querySelector('.head__lead')?.textContent).toContain('2 de ellas son de prioridad alta');
  });

  it('dibuja el Pareto ordenado y la tabla cruzada con totales', async () => {
    api.stats.and.returnValue(of(STATS));
    await create();
    const labels = Array.from(el.querySelectorAll('.bar__label')).map((n) => n.textContent);
    expect(labels).toEqual(['Abierto', 'Completado', 'En progreso']);
    const footer = Array.from(el.querySelectorAll('tfoot td')).map((n) => n.textContent?.trim());
    expect(footer).toEqual(['3', '1', '2', '6']);
  });

  it('usa singular cuando solo una pendiente es de prioridad alta', async () => {
    api.stats.and.returnValue(
      of({ ...STATS, matrix: { ...STATS.matrix, open: { high: 1, medium: 2, low: 0 } } }),
    );
    await create();
    expect(el.querySelector('.head__lead')?.textContent).toContain('Una de ellas es de prioridad alta');
  });

  it('muestra el error del API y permite reintentar', async () => {
    api.stats.and.returnValue(
      throwError(() => ({ status: 403, code: 'forbidden', message: 'No tiene permisos' })),
    );
    await create();
    expect(el.querySelector('[role=alert]')?.textContent).toContain('No tiene permisos');

    api.stats.and.returnValue(of(STATS));
    el.querySelector<HTMLButtonElement>('.alert .btn')!.click();
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')).toBeNull();
    expect(api.stats).toHaveBeenCalledTimes(2);
  });
});
