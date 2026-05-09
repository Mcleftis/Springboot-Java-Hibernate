import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarketDataService, MarketData } from '../../services/market-data.service';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  public chart: any;
  public analysis: any = null;
  public lstm: any = null;

  constructor(
    private ds: MarketDataService,
    private cdr: ChangeDetectorRef // <--- ΠΡΟΣΘΗΚΗ 1: Ο "ξυπνητήρης" της Angular
  ) {}

  ngOnInit(): void {
    // 1. Ζητάμε τα δεδομένα του γραφήματος
    this.ds.getData().subscribe({
      next: (data) => {
        this.createChart(data);
        
        // 2. Ζητάμε το AI
        this.ds.getAnalysis('GOLD').subscribe({
          next: (res) => {
            const parsed = typeof res === 'string' ? JSON.parse(res) : res;
            this.analysis = parsed?.quant ?? null;
            this.lstm = parsed?.lstm ?? null;
            
            // 3. Βάζουμε τις προβλέψεις
            if (this.lstm && this.lstm.predictions) {
              this.addPredictions(this.lstm.predictions);
            }

            // <--- ΠΡΟΣΘΗΚΗ 2: ΤΟ ΜΑΓΙΚΟ ΚΟΛΠΟ --->
            // Λέμε στην Angular: "Ήρθαν νέα δεδομένα, κάνε ΑΜΕΣΩΣ refresh το HTML!"
            this.cdr.detectChanges(); 
          },
          error: (err) => console.error("Sfalma AI:", err)
        });
      },
      error: (err) => console.error("Sfalma Vashs:", err)
    });
  }

  createChart(data: MarketData[]) {
    if (this.chart) this.chart.destroy();
    const labels = data.map(item => item.recordDate);
    const prices = data.map(item => item.close);
    
    this.chart = new Chart('marketChart', {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Gold Price',
          data: prices,
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
    if(!this.chart || !preds) return;
    
    const futureLabels = preds.map((_, i) => 'T+'+(i+1));
    const nulls = Array(this.chart.data.labels.length - 1).fill(null);
    const lastPrice = this.chart.data.datasets[0].data[this.chart.data.datasets[0].data.length - 1];
    
    this.chart.data.labels.push(...futureLabels);
    this.chart.data.datasets[0].data.push(...Array(preds.length).fill(null));
    
    this.chart.data.datasets.push({
        label: 'LSTM Prediction',
        data: [...nulls, lastPrice, ...preds],
        borderColor: 'purple',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 3
    });
    this.chart.update();
  }
}