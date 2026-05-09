package com.dealership.quant_trading;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:4200")
public class AnalysisController {

    @Autowired
    private MarketDataRepository repository;

    @GetMapping("/analysis/{symbol}")
    public ResponseEntity<?> getAnalysis(@PathVariable String symbol) {
        try {
            List<MarketData> data = repository.findAll();
            if (data.isEmpty()) return ResponseEntity.status(404).body(Map.of("error", "No data"));
            double gains = 0, losses = 0;
            if (data.size() >= 15) {
                for (int i = data.size() - 14; i < data.size(); i++) {
                    double change = data.get(i).getClose() - data.get(i-1).getClose();
                    if (change > 0) gains += change; else losses += Math.abs(change);
                }
            }
            double rsi = losses == 0 ? 100.0 : 100 - (100 / (1 + gains/losses));
            double support = data.stream().mapToDouble(MarketData::getClose).min().orElse(0);
            double resistance = data.stream().mapToDouble(MarketData::getClose).max().orElse(0);
            String condition = rsi > 70 ? "OVERBOUGHT" : rsi < 30 ? "OVERSOLD" : "NEUTRAL";
            Map<String,Object> quant = new HashMap<>();
            quant.put("symbol", symbol); quant.put("condition", condition);
            quant.put("rsi", rsi); quant.put("supportZone", support);
            quant.put("resistanceZone", resistance); quant.put("riskLevel", rsi/100.0);
            quant.put("recommendation", condition + " | RSI=" + String.format("%.1f", rsi));
            Map<String,Object> lstm = new HashMap<>();
            lstm.put("predictions", List.of()); lstm.put("trend", "N/A"); lstm.put("confidence", 0.0);
            return ResponseEntity.ok(Map.of("quant", quant, "lstm", lstm));
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of("error", e.getMessage()));
        }
    }
}