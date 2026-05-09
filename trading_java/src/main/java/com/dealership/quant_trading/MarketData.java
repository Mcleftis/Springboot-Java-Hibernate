package com.dealership.quant_trading;
import jakarta.persistence.*;
import java.time.LocalDate;
@Entity
@Table(name = "market_data")
public class MarketData {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private LocalDate recordDate;
    private Double open;
    private Double high;
    private Double low;
    private Double close;
    private Long volume;
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public LocalDate getRecordDate() { return recordDate; }
    public void setRecordDate(LocalDate recordDate) { this.recordDate = recordDate; }
    public Double getOpen() { return open; }
    public void setOpen(Double open) { this.open = open; }
    public Double getHigh() { return high; }
    public void setHigh(Double high) { this.high = high; }
    public Double getLow() { return low; }
    public void setLow(Double low) { this.low = low; }
    public Double getClose() { return close; }
    public void setClose(Double close) { this.close = close; }
    public Long getVolume() { return volume; }
    public void setVolume(Long volume) { this.volume = volume; }
}