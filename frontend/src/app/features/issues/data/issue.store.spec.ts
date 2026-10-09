import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { IssueApiService } from '../../../core/issues/issue-api.service';
import { aSummary, anIssue } from '../../../testing/test-data';
import { IssueStore } from './issue.store';

describe('IssueStore', () => {
  let store: IssueStore;
  let api: jasmine.SpyObj<IssueApiService>;

  beforeEach(() => {
    api = jasmine.createSpyObj<IssueApiService>('IssueApiService', [
      'list',
      'summary',
      'create',
      'update',
      'resolve',
      'remove',
    ]);
    api.list.and.returnValue(of([anIssue()]));
    api.summary.and.returnValue(of(aSummary));

    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        IssueStore,
        { provide: IssueApiService, useValue: api },
      ],
    });
    store = TestBed.inject(IssueStore);
  });

  it('load obtiene incidencias y resumen', async () => {
    await store.load();
    expect(store.issues().length).toBe(1);
    expect(store.summary()).toEqual(aSummary);
    expect(store.loading()).toBeFalse();
  });

  it('load expone el mensaje de error del API', async () => {
    api.list.and.returnValue(
      throwError(() => ({ status: 503, code: 'x', message: 'Servicio no disponible' })),
    );
    await store.load();
    expect(store.error()).toBe('Servicio no disponible');
    expect(store.loading()).toBeFalse();
  });

  it('load usa un mensaje genérico ante errores desconocidos', async () => {
    api.summary.and.returnValue(throwError(() => new Error('boom')));
    await store.load();
    expect(store.error()).toContain('error inesperado');
  });

  it('setFilters recarga con los nuevos filtros', async () => {
    await store.setFilters({ status: 'open', priority: null });
    expect(api.list).toHaveBeenCalledWith({ status: 'open', priority: null });
    expect(store.hasActiveFilters()).toBeTrue();
  });

  it('setFilters no recarga si los filtros no cambian', async () => {
    await store.setFilters({ status: null, priority: null });
    expect(api.list).not.toHaveBeenCalled();
  });

  it('update reemplaza la incidencia y refresca el resumen', async () => {
    await store.load();
    api.update.and.returnValue(of(anIssue({ status: 'completed' })));
    await store.update('i1', { status: 'completed' });
    expect(store.issues()[0].status).toBe('completed');
    expect(api.summary).toHaveBeenCalledTimes(2);
    expect(store.isPending('i1')).toBeFalse();
  });

  it('update retira la incidencia si deja de cumplir el filtro activo', async () => {
    await store.setFilters({ status: 'open', priority: null });
    api.update.and.returnValue(of(anIssue({ status: 'in_progress' })));
    await store.update('i1', { status: 'in_progress' });
    expect(store.issues().length).toBe(0);
  });

  it('update informa el error y libera el estado pendiente', async () => {
    await store.load();
    api.update.and.returnValue(throwError(() => ({ status: 404, code: 'nf', message: 'No existe' })));
    await store.update('i1', { status: 'completed' });
    expect(store.error()).toBe('No existe');
    expect(store.isPending('i1')).toBeFalse();
  });

  it('create registra y recarga el listado', async () => {
    api.create.and.returnValue(of(anIssue({ id: 'nuevo' })));
    const created = await store.create({ title: 'Nueva', description: '', priority: 'low' });
    expect(created.id).toBe('nuevo');
    expect(api.list).toHaveBeenCalled();
  });

  it('resolve marca la incidencia como completada y refresca el resumen', async () => {
    await store.load();
    api.resolve.and.returnValue(of(anIssue({ status: 'completed' })));
    await store.resolve('i1');
    expect(store.issues()[0].status).toBe('completed');
    expect(api.summary).toHaveBeenCalledTimes(2);
  });

  it('resolve muestra el 403 del API sin alterar el listado', async () => {
    await store.load();
    api.resolve.and.returnValue(
      throwError(() => ({ status: 403, code: 'forbidden', message: 'Sin permisos' })),
    );
    await store.resolve('i1');
    expect(store.error()).toBe('Sin permisos');
    expect(store.issues()[0].status).toBe('open');
  });

  it('remove quita la incidencia del listado', async () => {
    await store.load();
    api.remove.and.returnValue(of(undefined));
    await store.remove('i1');
    expect(store.issues().length).toBe(0);
    expect(store.isPending('i1')).toBeFalse();
  });
});
