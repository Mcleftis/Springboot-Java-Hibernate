import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface MarketData {
  id: number;
  recordDate: string;
  close: number;
}

export interface QuantAnalysis {
  symbol: string;
  condition: string;
  rsi: number;
  supportZone: number;
  resistanceZone: number;
  riskLevel: number;
  recommendation: string;
}

export interface LstmAnalysis {
  predictions: number[];
  trend: string;
  confidence: number;
}

export interface AnalysisResponse {
  quant: QuantAnalysis;
  lstm: LstmAnalysis;
}

@Injectable({ providedIn: 'root' })
export class MarketDataService {
  private baseUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  getData(): Observable<MarketData[]> {
    return this.http.get<MarketData[]>(this.baseUrl + '/market-data');
  }

  getAnalysis(symbol: string = 'GOLD'): Observable<AnalysisResponse> {
    return this.http.get<AnalysisResponse>(this.baseUrl + '/analysis/' + symbol);
  }
}