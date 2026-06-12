import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface MarketData {
  id: number;
  recordDate: string;
  close: number;
}

export interface QuantAnalysis {
  error?: string;
  symbol?: string;
  condition?: string;
  rsi?: number;
  supportZone?: number;
  resistanceZone?: number;
  riskLevel?: number;
  recommendation?: string;
}

export interface LstmAnalysis {
  error?: string;
  predictions?: number[];
  trend?: string;
  confidence?: number;
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
    return this.http.get<MarketData[]>(this.baseUrl + '/market-data').pipe(
      catchError(this.handleError)
    );
  }

  getAnalysis(symbol: string = 'GOLD'): Observable<AnalysisResponse> {
    return this.http.get<AnalysisResponse>(this.baseUrl + '/analysis/' + symbol).pipe(
      catchError(this.handleError)
    );
  }

  askRag(question: string): Observable<any> {
    return this.http.post<any>(this.baseUrl + '/rag/ask', { question: question }).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse) {
    console.error('API Fault Detected:', error.message, error);
    return throwError(() => new Error('API communication error. Check console logs.'));
  }
}