import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Το νέο Interface που ταιριάζει ακριβώς με τη βάση μας
export interface MarketData { 
  id: number; 
  recordDate: string; 
  close: number; 
}

@Injectable({ providedIn: 'root' })
export class MarketDataService {
  private url = 'http://localhost:8080/api/market-data';

  constructor(private http: HttpClient) { }

  getData(): Observable<MarketData[]> { 
    return this.http.get<MarketData[]>(this.url); 
  }
}