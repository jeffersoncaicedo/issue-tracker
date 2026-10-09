/**
 * Geometría de los gráficos del resumen (funciones puras, sin Angular).
 * Separarla de la plantilla permite probar los cálculos de forma aislada.
 */

import { ISSUE_PRIORITIES, ISSUE_STATUSES, IssuePriority, IssueStatus } from '../../core/models/issue.models';

export interface DonutSegment {
  readonly status: IssueStatus;
  readonly count: number;
  readonly percent: number;
  /** `stroke-dasharray` y `stroke-dashoffset` del arco sobre un círculo. */
  readonly dashArray: string;
  readonly dashOffset: number;
}

export interface ParetoBar {
  readonly status: IssueStatus;
  readonly count: number;
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
  /** Porcentaje acumulado hasta esta categoría (0-100). */
  readonly cumulative: number;
  readonly pointX: number;
  readonly pointY: number;
}

export interface ParetoChart {
  readonly bars: readonly ParetoBar[];
  readonly linePoints: string;
  readonly maxCount: number;
  /** Coordenada Y de la línea de referencia del 80 %. */
  readonly y80: number;
}

export interface PriorityRow {
  readonly priority: IssuePriority;
  readonly total: number;
  /** Ancho relativo de la barra respecto a la prioridad con más incidencias (0-100). */
  readonly widthPercent: number;
  readonly segments: readonly { readonly status: IssueStatus; readonly count: number }[];
}

/** Dimensiones del área de dibujo del Pareto (unidades del viewBox). */
export const PARETO_BOX = { width: 360, height: 220, top: 20, right: 44, bottom: 36, left: 36 } as const;

/** Porcentaje entero seguro (sin división entre cero). */
export function percentOf(part: number, total: number): number {
  return total > 0 ? Math.round((part / total) * 100) : 0;
}

/**
 * Arcos del gráfico de anillo. Se dibujan como trazos sobre un círculo de radio
 * `radius`, separados por un pequeño hueco cuando hay más de un segmento.
 */
export function buildDonut(
  byStatus: Readonly<Record<IssueStatus, number>>,
  radius: number,
  gap = 3,
): DonutSegment[] {
  const total = ISSUE_STATUSES.reduce((sum, s) => sum + byStatus[s], 0);
  if (total === 0) return [];

  const circumference = 2 * Math.PI * radius;
  const visible = ISSUE_STATUSES.filter((s) => byStatus[s] > 0);
  const effectiveGap = visible.length > 1 ? gap : 0;
  let offset = 0;

  return visible.map((status) => {
    const count = byStatus[status];
    const length = (count / total) * circumference;
    const drawn = Math.max(length - effectiveGap, 0.5);
    const segment: DonutSegment = {
      status,
      count,
      percent: percentOf(count, total),
      dashArray: `${drawn.toFixed(2)} ${(circumference - drawn).toFixed(2)}`,
      dashOffset: -offset,
    };
    offset += length;
    return segment;
  });
}

/**
 * Diagrama de Pareto: categorías ordenadas de mayor a menor con su porcentaje
 * acumulado. Con empate se respeta el orden natural del flujo de trabajo.
 */
export function buildPareto(byStatus: Readonly<Record<IssueStatus, number>>): ParetoChart {
  const { width, height, top, right, bottom, left } = PARETO_BOX;
  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const total = ISSUE_STATUSES.reduce((sum, s) => sum + byStatus[s], 0);
  const maxCount = Math.max(...ISSUE_STATUSES.map((s) => byStatus[s]), 1);

  const ordered = [...ISSUE_STATUSES].sort((a, b) => byStatus[b] - byStatus[a]);
  const slot = plotW / ordered.length;
  const barWidth = slot * 0.56;
  let accumulated = 0;

  const bars = ordered.map((status, i) => {
    const count = byStatus[status];
    accumulated += count;
    const barHeight = (count / maxCount) * plotH;
    const cumulative = total > 0 ? (accumulated / total) * 100 : 0;
    const centerX = left + slot * i + slot / 2;
    return {
      status,
      count,
      x: centerX - barWidth / 2,
      y: top + plotH - barHeight,
      width: barWidth,
      height: barHeight,
      cumulative: Math.round(cumulative),
      pointX: centerX,
      pointY: top + plotH - (cumulative / 100) * plotH,
    };
  });

  return {
    bars,
    linePoints: bars.map((b) => `${b.pointX.toFixed(1)},${b.pointY.toFixed(1)}`).join(' '),
    maxCount,
    y80: top + plotH - 0.8 * plotH,
  };
}

/** Barras apiladas por prioridad, comparables entre sí (escala común). */
export function buildPriorityRows(
  matrix: Readonly<Record<IssueStatus, Readonly<Record<IssuePriority, number>>>>,
): PriorityRow[] {
  const totals = ISSUE_PRIORITIES.map((p) =>
    ISSUE_STATUSES.reduce((sum, s) => sum + matrix[s][p], 0),
  );
  const max = Math.max(...totals, 1);
  return ISSUE_PRIORITIES.map((priority, i) => ({
    priority,
    total: totals[i],
    widthPercent: (totals[i] / max) * 100,
    segments: ISSUE_STATUSES.map((status) => ({ status, count: matrix[status][priority] })).filter(
      (seg) => seg.count > 0,
    ),
  }));
}
