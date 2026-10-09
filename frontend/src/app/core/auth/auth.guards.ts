import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Permission } from '../models/auth.models';
import { AuthService } from './auth.service';

/** Protege las rutas privadas; conserva la URL solicitada para volver tras el login. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  return auth.isAuthenticated()
    ? true
    : inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

/** Evita mostrar el login a un usuario que ya tiene sesión activa. */
export const guestGuard: CanActivateFn = () =>
  inject(AuthService).isAuthenticated() ? inject(Router).createUrlTree(['/issues']) : true;

/** Restringe una ruta a usuarios con un permiso concreto (p. ej. la vista de resumen). */
export function permissionGuard(permission: Permission): CanActivateFn {
  return () =>
    inject(AuthService).can(permission) ? true : inject(Router).createUrlTree(['/issues']);
}
