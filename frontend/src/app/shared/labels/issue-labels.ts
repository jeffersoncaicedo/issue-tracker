import { IssuePriority, IssueStatus } from '../../core/models/issue.models';

/** Textos visibles en la interfaz (los valores del API se mantienen en inglés). */
export const STATUS_LABELS: Readonly<Record<IssueStatus, string>> = {
  open: 'Abierto',
  in_progress: 'En progreso',
  completed: 'Completado',
};

export const PRIORITY_LABELS: Readonly<Record<IssuePriority, string>> = {
  high: 'Alta',
  medium: 'Media',
  low: 'Baja',
};

/** Nivel numérico usado para dibujar el indicador de prioridad. */
export const PRIORITY_LEVEL: Readonly<Record<IssuePriority, 1 | 2 | 3>> = {
  high: 3,
  medium: 2,
  low: 1,
};
