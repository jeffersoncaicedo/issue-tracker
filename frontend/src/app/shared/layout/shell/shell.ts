import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../../core/auth/auth.service';
import { ROLE_LABELS } from '../../../core/models/auth.models';

/** Marco de las páginas autenticadas: cabecera con usuario y cierre de sesión. */
@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Shell {
  protected readonly auth = inject(AuthService);
  protected readonly loggingOut = signal(false);
  protected readonly roleLabels = ROLE_LABELS;

  protected logout(): void {
    this.loggingOut.set(true);
    this.auth.logout().subscribe({ complete: () => this.loggingOut.set(false) });
  }
}
