import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MarketDataService, MarketData, AnalysisResponse } from '../../services/market-data.service';
import Chart from 'chart.js/auto';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit, OnDestroy {
  public chart?: Chart;
  public analysis: any = null;
  public lstm: any = null;
  
  public ragQuestion: string = '';
  public ragAnswer: string = '';
  public isRagLoading: boolean = false;

  private subscriptions: Subscription = new Subscription();

  constructor(private ds: MarketDataService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    const dataSub = this.ds.getData().subscribe({
      next: (data: MarketData[]) => {
        this.createChart(data);
        
        const aiSub = this.ds.getAnalysis('GOLD').subscribe({
          next: (res: AnalysisResponse) => {
            this.analysis = res.quant ?? null;
            this.lstm = res.lstm ?? null;
            
            if (this.lstm && this.lstm.predictions) {
               this.addPredictions(this.lstm.predictions);
            }
            this.cdr.detectChanges(); 
          },
          error: (err) => console.error("F12 Log - Σφάλμα AI (Java/Python):", err)
        });
        
        this.subscriptions.add(aiSub);
      },
      error: (err) => console.error("F12 Log - Σφάλμα Βάσης (Java/DB):", err)
    });

    this.subscriptions.add(dataSub);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.chart) {
      this.chart.destroy();
    }
  }

  askRagExpert() {
    if (!this.ragQuestion.trim()) return;
    this.isRagLoading = true;
    this.ragAnswer = '';
    
    const ragSub = this.ds.askRag(this.ragQuestion).subscribe({
      next: (res) => {
        this.ragAnswer = res.data?.answer || "Δεν ελήφθη απάντηση από το RAG.";
        this.isRagLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error("F12 Log - Σφάλμα RAG:", err);
        this.ragAnswer = "Σφάλμα επικοινωνίας με το RAG σύστημα.";
        this.isRagLoading = false;
        this.cdr.detectChanges();
      }
    });

    this.subscriptions.add(ragSub);
  }

  createChart(data: MarketData[]) {
    if (this.chart) this.chart.destroy();
    
    const labels = data.map(item => item.recordDate);
    const pointData = data.map(item => ({ x: item.recordDate, y: item.close }));

    this.chart = new Chart('marketChart', {
      type: 'line',
      data: { 
        labels: labels, 
        datasets: [{ 
          label: 'Gold Price', 
          data: pointData, 
          borderColor: 'blue', 
          borderWidth: 2, 
          fill: false, 
          pointRadius: 0 
        }] 
      },
      options: { responsive: true, animation: false }
    });
  }

  addPredictions(preds: number[]) {
    if(!this.chart || !this.chart.data.labels || !preds) return;

    const futureLabels = preds.map((_, i) => 'T+'+(i+1));
    this.chart.data.labels.push(...futureLabels);

    const historicalData = this.chart.data.datasets[0].data as {x: string, y: number}[];
    const lastPoint = historicalData[historicalData.length - 1];

    const lstmData = [
      { x: lastPoint.x, y: lastPoint.y },
      ...preds.map((pred, i) => ({ x: futureLabels[i], y: pred }))
    ];

    this.chart.data.datasets.push({ 
      label: 'LSTM Prediction', 
      data: lstmData as any, 
      borderColor: 'purple', 
      borderWidth: 2, 
      borderDash: [5, 5], 
      fill: false, 
      pointRadius: 3 
    });
    
    this.chart.update();
  }
}