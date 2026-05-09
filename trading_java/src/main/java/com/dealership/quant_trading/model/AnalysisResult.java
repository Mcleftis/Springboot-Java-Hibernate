package com.dealership.fleet_manager.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "analysis_results")
public class AnalysisResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String symbol;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CyclePhase cyclePhase;   // ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private MarketCondition condition;  // OVERBOUGHT, OVERSOLD, NEUTRAL

    @Column
    private Double supportZone;      

    @Column
    private Double resistanceZone;   

    @Column
    private Double riskLevel;        // 0.0 - 1.0

    @Column(length = 1000)
    private String recommendation; 

    @Column
    private LocalDateTime analyzedAt = LocalDateTime.now();

    public enum CyclePhase {
        ACCUMULATION,
        MARKUP,
        DISTRIBUTION,
        MARKDOWN
    }

    public enum MarketCondition {
        OVERBOUGHT,
        OVERSOLD,
        NEUTRAL
    }
}