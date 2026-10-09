import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { aSummary } from '../../../../testing/test-data';
import { SummaryBar } from './summary-bar';

describe('SummaryBar', () => {
  let fixture: ComponentFixture<SummaryBar>;
  let el: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SummaryBar],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();
    fixture = TestBed.createComponent(SummaryBar);
    fixture.componentRef.setInput('summary', aSummary);
    await fixture.whenStable();
    el = fixture.nativeElement;
  });

  it('muestra el total y la cantidad por estado', () => {
    expect(el.querySelector('.summary__number')?.textContent?.trim()).toBe('4');
    const counts = Array.from(el.querySelectorAll('.legend__count')).map((n) => n.textContent);
    expect(counts).toEqual(['2', '1', '1']);
  });

  it('muestra la cantidad ANTES de la etiqueta para no confundirla con el porcentaje', () => {
    const item = el.querySelector('.legend__item')!;
    const order = Array.from(item.children).map((c) => c.className);
    expect(order.indexOf('legend__count')).toBeLessThan(order.indexOf('legend__label'));
    expect(order.indexOf('legend__label')).toBeLessThan(order.indexOf('legend__percent'));
  });

  it('calcula porcentajes', () => {
    const percents = Array.from(el.querySelectorAll('.legend__percent')).map((n) => n.textContent);
    expect(percents).toEqual(['50 %', '25 %', '25 %']);
  });

  it('emite el estado al pulsar y null al volver a pulsar el activo', async () => {
    const emitted: (string | null)[] = [];
    fixture.componentInstance.statusToggled.subscribe((s) => emitted.push(s));

    const openBtn = el.querySelector<HTMLButtonElement>('.legend__item')!;
    openBtn.click();
    fixture.componentRef.setInput('activeStatus', 'open');
    await fixture.whenStable();
    expect(openBtn.getAttribute('aria-pressed')).toBe('true');
    openBtn.click();

    expect(emitted).toEqual(['open', null]);
  });

  it('maneja un resumen vacío sin dividir entre cero', async () => {
    fixture.componentRef.setInput('summary', { total: 0, open: 0, in_progress: 0, completed: 0 });
    await fixture.whenStable();
    expect(el.querySelector('.bar__segment--empty')).not.toBeNull();
    expect(el.querySelector('.legend__percent')?.textContent).toBe('0 %');
  });
});
