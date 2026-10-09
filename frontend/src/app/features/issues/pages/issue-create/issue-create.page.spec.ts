import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { anIssue } from '../../../../testing/test-data';
import { IssueStore } from '../../data/issue.store';
import { IssueCreatePage } from './issue-create.page';

describe('IssueCreatePage', () => {
  let fixture: ComponentFixture<IssueCreatePage>;
  let store: jasmine.SpyObj<IssueStore>;
  let el: HTMLElement;

  beforeEach(async () => {
    store = jasmine.createSpyObj<IssueStore>('IssueStore', ['create']);
    await TestBed.configureTestingModule({
      imports: [IssueCreatePage],
      providers: [
        provideZonelessChangeDetection(),
        provideRouter([]),
        { provide: IssueStore, useValue: store },
      ],
    }).compileComponents();
    spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    fixture = TestBed.createComponent(IssueCreatePage);
    el = fixture.nativeElement;
    await fixture.whenStable();
  });

  function type(selector: string, value: string): void {
    const input = el.querySelector<HTMLInputElement>(selector)!;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  async function submit(): Promise<void> {
    el.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  }

  it('prioridad "media" seleccionada por defecto', () => {
    const checked = el.querySelector<HTMLInputElement>('input[type=radio]:checked');
    expect(checked?.value).toBe('medium');
  });

  it('no envía y muestra errores si el título es inválido', async () => {
    type('#title', '  a ');
    await submit();
    expect(store.create).not.toHaveBeenCalled();
    expect(el.querySelector('#title-error')?.textContent).toContain('al menos 3');
  });

  it('crea la incidencia y vuelve al listado', async () => {
    store.create.and.resolveTo(anIssue());
    type('#title', '  Error al exportar  ');
    type('#description', 'Detalle');
    el.querySelector<HTMLInputElement>('input[value=high]')!.click();
    await submit();

    expect(store.create).toHaveBeenCalledWith({
      title: 'Error al exportar',
      description: 'Detalle',
      priority: 'high',
    });
    expect(TestBed.inject(Router).navigate).toHaveBeenCalledWith(['/issues']);
  });

  it('muestra el error del API', async () => {
    store.create.and.rejectWith({ status: 503, code: 'x', message: 'Servicio no disponible' });
    type('#title', 'Título válido');
    await submit();
    await fixture.whenStable();
    expect(el.querySelector('[role=alert]')?.textContent).toContain('Servicio no disponible');
  });
});
