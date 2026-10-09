import { buildDonut, buildPareto, buildPriorityRows, PARETO_BOX, percentOf } from './chart-geometry';

describe('chart-geometry', () => {
  const byStatus = { open: 2, in_progress: 1, completed: 5 };

  describe('percentOf', () => {
    it('calcula porcentajes enteros y evita dividir entre cero', () => {
      expect(percentOf(1, 4)).toBe(25);
      expect(percentOf(1, 3)).toBe(33);
      expect(percentOf(3, 0)).toBe(0);
    });
  });

  describe('buildDonut', () => {
    const radius = 70;
    const circumference = 2 * Math.PI * radius;

    it('devuelve un segmento por estado con datos y porcentajes', () => {
      const segs = buildDonut(byStatus, radius);
      expect(segs.map((s) => s.status)).toEqual(['open', 'in_progress', 'completed']);
      expect(segs.map((s) => s.percent)).toEqual([25, 13, 63]);
    });

    it('los desplazamientos son acumulativos', () => {
      const segs = buildDonut(byStatus, radius);
      expect(segs[0].dashOffset).toBeCloseTo(-0);
      expect(segs[1].dashOffset).toBeCloseTo(-(2 / 8) * circumference);
      expect(segs[2].dashOffset).toBeCloseTo(-(3 / 8) * circumference);
    });

    it('un único estado ocupa el anillo completo, sin hueco', () => {
      const [seg] = buildDonut({ open: 0, in_progress: 0, completed: 4 }, radius);
      expect(Number(seg.dashArray.split(' ')[0])).toBeCloseTo(circumference, 1);
    });

    it('sin datos no hay segmentos', () => {
      expect(buildDonut({ open: 0, in_progress: 0, completed: 0 }, radius)).toEqual([]);
    });
  });

  describe('buildPareto', () => {
    it('ordena de mayor a menor y acumula hasta 100 %', () => {
      const chart = buildPareto(byStatus);
      expect(chart.bars.map((b) => b.status)).toEqual(['completed', 'open', 'in_progress']);
      expect(chart.bars.map((b) => b.cumulative)).toEqual([63, 88, 100]);
      expect(chart.maxCount).toBe(5);
    });

    it('la barra mayor ocupa toda la altura útil', () => {
      const { bars } = buildPareto(byStatus);
      expect(bars[0].y).toBeCloseTo(PARETO_BOX.top);
      expect(bars[0].height).toBeGreaterThan(bars[1].height);
    });

    it('sin datos produce barras de altura cero y acumulado 0', () => {
      const chart = buildPareto({ open: 0, in_progress: 0, completed: 0 });
      expect(chart.bars.every((b) => b.height === 0 && b.cumulative === 0)).toBeTrue();
    });
  });

  describe('buildPriorityRows', () => {
    it('totaliza por prioridad con una escala común', () => {
      const rows = buildPriorityRows({
        open: { high: 2, medium: 0, low: 1 },
        in_progress: { high: 1, medium: 0, low: 0 },
        completed: { high: 1, medium: 2, low: 0 },
      });
      expect(rows.map((r) => r.total)).toEqual([4, 2, 1]);
      expect(rows.map((r) => r.widthPercent)).toEqual([100, 50, 25]);
      expect(rows[1].segments).toEqual([{ status: 'completed', count: 2 }]);
    });
  });
});
