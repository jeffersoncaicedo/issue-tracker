import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmDialog } from './confirm-dialog';

describe('ConfirmDialog', () => {
  let fixture: ComponentFixture<ConfirmDialog>;
  let el: HTMLElement;
  const options = { title: 'Eliminar', message: '¿Seguro?', confirmLabel: 'Eliminar', tone: 'danger' as const };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfirmDialog],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();
    fixture = TestBed.createComponent(ConfirmDialog);
    el = fixture.nativeElement;
    await fixture.whenStable();
  });

  /**
   * Devuelve la promesa dentro de un objeto: si una función `async` devolviera
   * la promesa directamente, `await` la aplanaría y esperaría la respuesta.
   */
  async function openDialog(): Promise<{ result: Promise<boolean> }> {
    const result = fixture.componentInstance.open(options);
    await fixture.whenStable();
    return { result };
  }

  it('abre un diálogo modal con el contenido indicado', async () => {
    await openDialog();
    const dialog = el.querySelector('dialog')!;
    expect(dialog.open).toBeTrue();
    expect(dialog.textContent).toContain('¿Seguro?');
    expect(el.querySelector('.btn--danger')?.textContent?.trim()).toBe('Eliminar');
    dialog.close();
  });

  it('resuelve true al confirmar', async () => {
    const { result } = await openDialog();
    el.querySelector<HTMLButtonElement>('button[value=confirm]')!.click();
    expect(await result).toBeTrue();
  });

  it('resuelve false al cancelar', async () => {
    const { result } = await openDialog();
    el.querySelector<HTMLButtonElement>('button[value=cancel]')!.click();
    expect(await result).toBeFalse();
  });

  it('resuelve false al cerrar con Esc o por código', async () => {
    const { result } = await openDialog();
    el.querySelector('dialog')!.close();
    expect(await result).toBeFalse();
  });
});
