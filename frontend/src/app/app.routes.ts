import { Routes } from '@angular/router';

import { authGuard, guestGuard, permissionGuard } from './core/auth/auth.guards';

/**
 * Todas las funcionalidades se cargan de forma diferida (lazy loading):
 * el bundle inicial solo contiene el arranque, el enrutador y los guards.
 */
export const routes: Routes = [
  {
    path: 'login',
    title: 'Iniciar sesión',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login/login.page').then((m) => m.LoginPage),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/layout/shell/shell').then((m) => m.Shell),
    children: [
      {
        path: 'issues',
        loadChildren: () =>
          import('./features/issues/issues.routes').then((m) => m.ISSUES_ROUTES),
      },
      {
        path: 'dashboard',
        title: 'Resumen',
        canActivate: [permissionGuard('stats:view')],
        loadComponent: () =>
          import('./features/dashboard/dashboard.page').then((m) => m.DashboardPage),
      },
      { path: '', pathMatch: 'full', redirectTo: 'issues' },
    ],
  },
  { path: '**', redirectTo: 'issues' },
];
