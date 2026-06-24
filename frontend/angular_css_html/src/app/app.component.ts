import { Component } from '@angular/core';
import { DashboardComponent } from './components/dashboard/dashboard.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [DashboardComponent], // Φέρνουμε ΜΟΝΟ το Dashboard, πετάξαμε το RouterOutlet
  // Αντί για HTML αρχείο, του λέμε "Ζωγράφισε το Dashboard ΚΑΤΕΥΘΕΙΑΝ"
  template: '<app-dashboard></app-dashboard>' 
})
export class AppComponent {
  title = 'quant-trading-ui';
}