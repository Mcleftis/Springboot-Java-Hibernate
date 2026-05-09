import { Component, OnInit } from '@angular/core';
import { MarketDataService, MarketData } from '../../services/market-data.service';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit {
  public chart: any;

  constructor(private ds: MarketDataService) {}

  ngOnInit(): void {
    this.ds.getData().subscribe(data => {
      this.createChart(data);
    });
  }

  createChart(data: MarketData[]) {
    // Αν υπάρχει ήδη γράφημα, το καταστρέφουμε για να μη γίνει διπλό
    if (this.chart) {
      this.chart.destroy();
    }

    // Κόβουμε τα δεδομένα. Παίρνουμε μόνο τις τελευταίες 500 μέρες.
    // Αλλιώς 8000+ σημεία θα "γονατίσουν" το rendering του Chrome.
    const recentData = data.slice(-500);

    // Διαβάζουμε τις νέες σωστές μεταβλητές (recordDate και close)
    const labels = recentData.map(item => item.recordDate);
    const prices = recentData.map(item => item.close);

    this.chart = new Chart('marketChart', {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Gold Price (Last 500 Days)',
          data: prices,
          borderColor: '#2ecc71',
          backgroundColor: 'rgba(46, 204, 113, 0.1)',
          borderWidth: 2,
          fill: true,
          pointRadius: 0, // Κρύβει τις τελείες για να φαίνεται σαν καθαρή γραμμή
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        animation: false, // Απενεργοποιούμε το animation για instant load
        plugins: {
          legend: { display: true }
        }
      }
    });
  }
}