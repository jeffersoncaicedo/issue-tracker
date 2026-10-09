import { provideZonelessChangeDetection, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AuthService } from '../../../../core/auth/auth.service';
import { Permission } from '../../../../core/models/auth.models';
import { EMPTY_FILTERS, Issue } from '../../../../core/models/issue.models';
import { aSummary, anIssue } from '../../../../testing/test-data';
import { IssueStore } from '../../data/issue.store';
import { IssueListPage } from './issue-list.page';

describe('IssueListPage', () => {
  let fixture: ComponentFixture<IssueListPage>;
  let el: HTMLElement;
  let store: jasmine.SpyObj<IssueStore>;

  const ISSUES: Issue[] = [
    anIssue({ id: 'a', title: 'Abierta', status: 'open' }),
    anIssue({ id: 'c', title: 'Cerrada', status: 'completed' }),
  ];

  async function create(permissions: Permission[]): Promise<void> {
    store = jasmine.createSpyObj<IssueStore>(
      'IssueStore',
      ['load', 'setFilters', 'update', 'resolve', 'remove', 'isPending'],
      {
        issues: signal(ISSUES),
        summary: signal(aSummary),
        filters: signal(EMPTY_FILTERS),
        loading: signal(false),
        error: signal(null),
        hasActiveFilters: signal(false),
      },
    );
    store.isPending.and.returnValue(false);
    store.load.and.resolveTo();
    store.remove.and.resolveTo();
    store.resolve.and.resolveTo();

    await TestBed.configureTestingModule({
      imports: [IssueListPage],
      providers: [
        provideZonelessChangeDetection(),
        provideRouter([]),
        { provide: AuthService, useValue: { can: (p: Permission) => permissions.includes(p) } },
      ],
    })
      .overrideComponent(IssueListPage, { set: { providers: [{ provide: IssueStore, useValue: store }] } })
      .compileComponents();
    fixture = TestBed.createComponent(IssueListPage);
    el = fixture.nativeElement;
    await fixture.whenStable();
  }

  /**
   * Pulsa un botón del diálogo y espera de forma determinista a que se cierre:
   * el evento `close` de <dialog> llega en una tarea posterior del navegador,
   * así que se espera el propio evento en lugar de un tiempo arbitrario.
   */
  async function answerDialog(value: 'confirm' | 'cancel'): Promise<void> {
    const dialog = el.querySelector('dialog')!;
    const closed = new Promise((resolve) => dialog.addEventListener('close', resolve, { once: true }));
    el.querySelector<HTMLButtonElement>(`button[value=${value}]`)!.click();
    await closed;
    await new Promise((resolve) => setTimeout(resolve)); // deja correr la continuación de remove()
    await fixture.whenStable();
  }

  const statusSelects = () => el.querySelectorAll<HTMLSelectElement>('select.status-select');

  describe('como usuario normal', () => {
    beforeEach(() => create([]));

    it('no muestra los botones Resolver ni Eliminar', () => {
      expect(el.querySelector('.btn--resolve')).toBeNull();
      expect(el.querySelector('.btn--quiet-danger')).toBeNull();
    });

    it('deshabilita la opción "Completado" y bloquea las incidencias completadas', () => {
      const [open, completed] = Array.from(statusSelects());
      const completedOption = Array.from(open.options).find((o) => o.value === 'completed')!;
      expect(completedOption.disabled).toBeTrue();
      expect(open.disabled).toBeFalse();
      expect(completed.disabled).toBeTrue();
    });
  });

  describe('como Administrador / Soporte', () => {
    beforeEach(() => create(['issues:resolve', 'issues:delete', 'stats:view']));

    it('muestra Resolver solo en incidencias no completadas y Eliminar en todas', () => {
      expect(el.querySelectorAll('.btn--resolve').length).toBe(1);
      expect(el.querySelectorAll('.btn--quiet-danger').length).toBe(2);
      expect(statusSelects()[1].disabled).toBeFalse();
    });

    it('Resolver delega en el store', () => {
      el.querySelector<HTMLButtonElement>('.btn--resolve')!.click();
      expect(store.resolve).toHaveBeenCalledWith('a');
    });

    it('Eliminar pide confirmación y solo elimina si se confirma', async () => {
      el.querySelector<HTMLButtonElement>('.btn--quiet-danger')!.click();
      await fixture.whenStable();
      const dialog = el.querySelector('dialog')!;
      expect(dialog.open).toBeTrue();
      expect(dialog.textContent).toContain('Abierta');

      await answerDialog('cancel');
      expect(store.remove).not.toHaveBeenCalled();

      el.querySelector<HTMLButtonElement>('.btn--quiet-danger')!.click();
      await fixture.whenStable();
      await answerDialog('confirm');
      expect(store.remove).toHaveBeenCalledWith('a');
    });
  });
});
