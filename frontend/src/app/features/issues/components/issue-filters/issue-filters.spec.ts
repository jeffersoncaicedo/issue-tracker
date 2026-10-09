import { provideZonelessChangeDetection } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EMPTY_FILTERS, IssueFilters } from '../../../../core/models/issue.models';
import { IssueFiltersBar } from './issue-filters';

describe('IssueFiltersBar', () => {
  let fixture: ComponentFixture<IssueFiltersBar>;
  let emitted: IssueFilters[];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IssueFiltersBar],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();
    fixture = TestBed.createComponent(IssueFiltersBar);
    fixture.componentRef.setInput('filters', EMPTY_FILTERS);
    emitted = [];
    fixture.componentInstance.filtersChange.subscribe((f) => emitted.push(f));
    await fixture.whenStable();
  });

  function select(id: string): HTMLSelectElement {
    return fixture.nativeElement.querySelector(`#${id}`);
  }

  it('emite los filtros al cambiar el estado', () => {
    const s = select('filter-status');
    s.selectedIndex = 3; // Completado
    s.dispatchEvent(new Event('change'));
    expect(emitted.at(-1)).toEqual({ status: 'completed', priority: null });
  });

  it('emite los filtros al cambiar la prioridad', () => {
    const p = select('filter-priority');
    p.selectedIndex = 1; // Alta
    p.dispatchEvent(new Event('change'));
    expect(emitted.at(-1)).toEqual({ status: null, priority: 'high' });
  });

  it('refleja filtros externos sin re-emitir y permite quitarlos', async () => {
    fixture.componentRef.setInput('filters', { status: 'open', priority: null });
    await fixture.whenStable();
    expect(select('filter-status').selectedIndex).toBe(1);
    expect(emitted.length).toBe(0);

    const clear = fixture.nativeElement.querySelector('.clear') as HTMLButtonElement;
    clear.click();
    expect(emitted.at(-1)).toEqual(EMPTY_FILTERS);
  });
});
