import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  signal,
  viewChild,
} from '@angular/core';

export interface ConfirmOptions {
  readonly title: string;
  readonly message: string;
  readonly confirmLabel: string;
  readonly cancelLabel?: string;
  /** `danger` resalta acciones destructivas (p. ej. eliminar). */
  readonly tone?: 'default' | 'danger';
}

/**
 * Diálogo de confirmación basado en el elemento nativo `<dialog>`:
 * modal, con foco atrapado y cierre con Esc gestionados por el navegador.
 * Uso: `if (await dialog.open({...})) { ... }`.
 */
@Component({
  selector: 'app-confirm-dialog',
  templateUrl: './confirm-dialog.html',
  styleUrl: './confirm-dialog.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfirmDialog {
  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');
  protected readonly options = signal<ConfirmOptions | null>(null);
  private resolver: ((confirmed: boolean) => void) | null = null;

  open(options: ConfirmOptions): Promise<boolean> {
    this.resolver?.(false); // un diálogo previo sin responder se considera cancelado
    this.options.set(options);
    const element = this.dialog().nativeElement;
    element.returnValue = '';
    element.showModal();
    return new Promise<boolean>((resolve) => (this.resolver = resolve));
  }

  /** Se dispara al cerrar por botón, Esc o `close()`. */
  protected onClose(): void {
    this.resolver?.(this.dialog().nativeElement.returnValue === 'confirm');
    this.resolver = null;
  }
}
