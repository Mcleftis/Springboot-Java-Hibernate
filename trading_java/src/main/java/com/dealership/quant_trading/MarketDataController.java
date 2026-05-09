package com.dealership.quant_trading.controller;

import com.dealership.quant_trading.MarketData;
import com.dealership.quant_trading.MarketDataRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:4200")
public class MarketDataController {

    @Autowired
    private MarketDataRepository repository;

    @GetMapping("/market-data")
    public List<MarketData> getMarketData() {
        List<MarketData> data = repository.findRecentData();
        Collections.reverse(data);
        return data;
    }

    @GetMapping("/analysis/{symbol}")
    public ResponseEntity<String> getAiAnalysis(@PathVariable String symbol) {
        List<MarketData> data = repository.findRecentData();
        Collections.reverse(data);
        
        List<Double> prices = data.stream().map(MarketData::getClose).collect(Collectors.toList());
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("symbol", symbol);
        payload.put("prices", prices);
        payload.put("steps", 5);

        RestTemplate rest = new RestTemplate();
        String q = "{}";
        String l = "{}";
        
        try {
            q = rest.postForObject("http://127.0.0.1:8003/wyckoff-full", payload, String.class);
        } catch (Exception e) {
            System.out.println("Quant AI Error: " + e.getMessage());
        }

        try {
            l = rest.postForObject("http://127.0.0.1:8004/predict", payload, String.class);
        } catch (Exception e) {
            System.out.println("LSTM AI Error: " + e.getMessage());
        }

        return ResponseEntity.ok("{\"quant\": " + q + ", \"lstm\": " + l + "}");
    }
}