import { Routes } from '@angular/router';

import { IssueStore } from './data/issue.store';

/** Rutas de la funcionalidad (cargadas de forma diferida desde app.routes.ts). */
export const ISSUES_ROUTES: Routes = [
  {
    path: '',
    providers: [IssueStore],
    children: [
      {
        path: '',
        title: 'Incidencias',
        loadComponent: () =>
          import('./pages/issue-list/issue-list.page').then((m) => m.IssueListPage),
      },
      {
        path: 'new',
        title: 'Nueva incidencia',
        loadComponent: () =>
          import('./pages/issue-create/issue-create.page').then((m) => m.IssueCreatePage),
      },
    ],
  },
];
