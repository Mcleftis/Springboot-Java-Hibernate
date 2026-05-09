import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class Api {
  private baseUrl = 'http://localhost:8080/api'; 

  constructor(private http: HttpClient) { }

  getMarketData(): Observable<any> {
    return this.http.get(`${this.baseUrl}/market-data`);
  }

  analyzeRag(query: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/rag/analyze`, { question: query });
  }
}