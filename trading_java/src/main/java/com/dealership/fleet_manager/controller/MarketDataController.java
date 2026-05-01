package com.dealership.fleet_manager.controller;
import com.dealership.fleet_manager.model.AnalysisResult;
import com.dealership.fleet_manager.model.MarketData;
import com.dealership.fleet_manager.service.AnalysisService;
import com.dealership.fleet_manager.service.MarketDataService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
@RestController
@RequestMapping("/api/market")
@RequiredArgsConstructor
public class MarketDataController {
    private final MarketDataService marketDataService;
    private final AnalysisService analysisService;
    private final RestTemplate restTemplate;
    @PostMapping("/upload/{symbol}")
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file, @PathVariable String symbol) {
        try {
            List<MarketData> saved = marketDataService.importFromCsv(file, symbol);
            return ResponseEntity.ok("Saved " + saved.size() + " records for " + symbol);
        } catch (Exception e) { return ResponseEntity.badRequest().body("Error: " + e.getMessage()); }
    }
    @GetMapping("/data/{symbol}")
    public ResponseEntity<List<MarketData>> getData(@PathVariable String symbol) {
        return ResponseEntity.ok(marketDataService.getBySymbol(symbol));
    }

    
    @PostMapping("/wyckoff-full/{symbol}")
    public ResponseEntity<String> wyckoffFull(@PathVariable String symbol) {
        try {
            List<MarketData> data = marketDataService.getBySymbol(symbol);
            List<Double> prices = data.stream().map(MarketData::getClose).collect(Collectors.toList());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = Map.of("symbol", symbol, "prices", prices);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.postForEntity("http://fleet-python:8002/wyckoff-full", request, String.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) { return ResponseEntity.badRequest().body("Error: " + e.getMessage()); }
    }
}
