package com.dealership.fleet_manager.model;

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
    private Double range;         // high - low (volatility indicator)

    @PrePersist
    public void calculate() {
        this.range = this.high - this.low;
        if (this.open != null && this.open != 0) {
            this.dailyReturn = ((this.close - this.open) / this.open) * 100;
        }
    }
}