package com.dealership.quant_trading.controller;

import com.dealership.quant_trading.model.MarketData;
import com.dealership.quant_trading.MarketDataRepository;
import java.util.*;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:4200")
public class MarketDataController {

    
    private static final Logger logger = LoggerFactory.getLogger(MarketDataController.class);

    @Autowired
    private MarketDataRepository repository;

    @GetMapping("/market-data")
    public List<MarketData> getMarketData() {
        List<MarketData> data = repository.findRecentData();
        Collections.reverse(data);
        return data;
    }

    @GetMapping("/analysis/{symbol}")
    public ResponseEntity<Map<String, Object>> getAiAnalysis(@PathVariable String symbol) {
        List<MarketData> data = repository.findRecentData();
        Collections.reverse(data);
        
        List<Double> prices = data.stream().map(MarketData::getClose).collect(Collectors.toList());
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("symbol", symbol);
        payload.put("prices", prices);
        payload.put("steps", 5);

        RestTemplate rest = new RestTemplate(); 
        
    
        Map<String, Object> response = new HashMap<>();
        
        try {
            Object q = rest.postForObject("http://127.0.0.1:8003/wyckoff-full", payload, Object.class);
            response.put("quant", q);
        } catch (Exception e) {
            logger.error("Quant AI Error: {}", e.getMessage()); 
            response.put("quant", Map.of("error", "Quant AI is offline")); 
        }

        try {
            Object l = rest.postForObject("http://127.0.0.1:8004/predict", payload, Object.class);
            response.put("lstm", l);
        } catch (Exception e) {
            logger.error("LSTM AI Error: {}", e.getMessage()); 
            response.put("lstm", Map.of("error", "LSTM AI is offline"));
        }

        
        return ResponseEntity.ok(response);
    }
}