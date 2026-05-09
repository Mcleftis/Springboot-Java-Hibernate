import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RagAnalysis } from './rag-analysis';

describe('RagAnalysis', () => {
  let component: RagAnalysis;
  let fixture: ComponentFixture<RagAnalysis>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RagAnalysis],
    }).compileComponents();

    fixture = TestBed.createComponent(RagAnalysis);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
