package com.dealership.quant_trading.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "market_data")
public class MarketData {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false)
    private String symbol; 
    @Column(nullable = false)
    private LocalDate date;
    @Column(nullable = false)
    private Double open;
    @Column(nullable = false)
    private Double high;
    @Column(nullable = false)
    private Double low;
    @Column(nullable = false)
    private Double close;
    @Column(nullable = false)
    private Long volume;
    @Column
    private Double dailyReturn;   
    @Column
    private Double range;

    @PrePersist
    public void calculate() {
        if (this.high != null && this.low != null) {
            this.range = this.high - this.low;
        } else {
            this.range = 0.0;
        }
        if (this.open != null && this.open != 0 && this.close != null) {
            this.dailyReturn = ((this.close - this.open) / this.open) * 100;
        } else {
            this.dailyReturn = 0.0;
        }
    }
}
