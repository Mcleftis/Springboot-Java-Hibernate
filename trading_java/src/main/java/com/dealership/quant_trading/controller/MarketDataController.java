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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api") // Αλλαγή για να πιάσουμε και το market-data και τα δικά σου
@CrossOrigin(origins = "http://localhost:4200") // ΤΟ ΚΛΕΙΔΙ ΓΙΑ ΝΑ ΠΕΡΑΣΟΥΝ ΤΑ ΔΕΔΟΜΕΝΑ ΣΤΗΝ ANGULAR
@RequiredArgsConstructor
public class MarketDataController {

    private final MarketDataService marketDataService;
    private final AnalysisService analysisService;
    private final RestTemplate restTemplate;

    // ΠΡΟΣΘΗΚΗ: Το endpoint που ψάχνει η Angular για το Dashboard
    @GetMapping("/market-data")
    public List<Map<String, Object>> getDashboardData() {
        List<Map<String, Object>> mockData = new ArrayList<>();
        Map<String, Object> row1 = new HashMap<>();
        row1.put("date", "2026-05-07T10:00:00Z");
        row1.put("price", 2350.50);
        mockData.add(row1);

        Map<String, Object> row2 = new HashMap<>();
        row2.put("date", "2026-05-06T10:00:00Z");
        row2.put("price", 1750.00);
        mockData.add(row2);

        return mockData;
    }

    // --- ΤΑ ΔΙΚΑ ΣΟΥ ENDPOINTS ΔΙΑΤΗΡΟΥΝΤΑΙ ΑΘΙΚΤΑ ΓΙΑ ΤΟ PYTHON TRADING AI ---

    @PostMapping("/market/upload/{symbol}")
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file, @PathVariable String symbol) {
        try {
            List<MarketData> saved = marketDataService.importFromCsv(file, symbol);
            return ResponseEntity.ok("Saved " + saved.size() + " records for " + symbol);
        } catch (Exception e) { return ResponseEntity.badRequest().body("Error: " + e.getMessage()); }
    }

    @GetMapping("/market/data/{symbol}")
    public ResponseEntity<List<MarketData>> getData(@PathVariable String symbol) {
        return ResponseEntity.ok(marketDataService.getBySymbol(symbol));
    }

    @PostMapping("/market/analyze/{symbol}")
    public ResponseEntity<AnalysisResult> analyze(@PathVariable String symbol) {
        return ResponseEntity.ok(analysisService.analyze(symbol));
    }

    @GetMapping("/market/analysis/{symbol}")
    public ResponseEntity<AnalysisResult> getAnalysis(@PathVariable String symbol) {
        return analysisService.getLatestAnalysis(symbol).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/market/wyckoff-full/{symbol}")
    public ResponseEntity<String> wyckoffFull(@PathVariable String symbol) {
        try {
            List<MarketData> data = marketDataService.getBySymbol(symbol);
            List<Double> prices = data.stream().map(MarketData::getClose).collect(Collectors.toList());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = Map.of("symbol", symbol, "prices", prices);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.postForEntity("http://fleet-python:8000/wyckoff-full", request, String.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) { return ResponseEntity.badRequest().body("Error: " + e.getMessage()); }
    }
}