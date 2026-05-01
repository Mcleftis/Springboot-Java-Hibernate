package com.dealership.fleet_manager.controller;

import com.dealership.fleet_manager.model.MarketData;
import com.dealership.fleet_manager.service.MarketDataService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * QuantController — Bridge από Java → Python quant_worker.py (port 8003).
 *
 * Αντικαθιστά πλήρως τον AnalysisController.java.
 * Η Java ΔΕΝ κάνει indicators. Απλώς:
 *  1. Τραβάει τα OHLCV δεδομένα από τη DB
 *  2. Τα πακετάρει σε JSON
 *  3. Τα στέλνει στην Python
 *  4. Επιστρέφει το αποτέλεσμα στο Frontend
 */
@RestController
@RequestMapping("/api/quant")
@RequiredArgsConstructor
public class QuantController {

    private static final Logger log = LoggerFactory.getLogger(QuantController.class);

    private static final String QUANT_WORKER_URL = "http://localhost:8003";

    private final MarketDataService marketDataService;
    private final RestTemplate restTemplate;

    // ─────────────────────────────────────────────
    // FULL ANALYSIS (RSI, MACD, ATR, Order Blocks, FVGs, Wyckoff)
    // ─────────────────────────────────────────────

    @PostMapping("/analyze/{symbol}")
    public ResponseEntity<?> analyze(@PathVariable String symbol) {
        log.info("QUANT ANALYSIS REQUEST → symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/analyze", payload, symbol);
    }

    // ─────────────────────────────────────────────
    // WYCKOFF FULL (με Volume, Springs, Upthrusts)
    // ─────────────────────────────────────────────

    @PostMapping("/wyckoff/{symbol}")
    public ResponseEntity<?> wyckoffFull(@PathVariable String symbol) {
        log.info("WYCKOFF ANALYSIS REQUEST → symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/wyckoff-full", payload, symbol);
    }

    // ─────────────────────────────────────────────
    // ORDER BLOCKS — Institutional Zones
    // ─────────────────────────────────────────────

    @PostMapping("/order-blocks/{symbol}")
    public ResponseEntity<?> orderBlocks(@PathVariable String symbol) {
        log.info("ORDER BLOCKS REQUEST → symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/order-blocks", payload, symbol);
    }

    // ─────────────────────────────────────────────
    // VOLUME PROFILE — POC, Value Area
    // ─────────────────────────────────────────────

    @PostMapping("/volume-profile/{symbol}")
    public ResponseEntity<?> volumeProfile(@PathVariable String symbol) {
        log.info("VOLUME PROFILE REQUEST → symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        // Volume Profile ΑΠΑΙΤΕΙ πραγματικό volume
        boolean hasVolume = data.stream().anyMatch(d -> d.getVolume() != null && d.getVolume() > 0);
        if (!hasVolume) {
            log.warn("VOLUME PROFILE SKIPPED — Symbol {} has no real volume data", symbol);
            return ResponseEntity.badRequest().body(Map.of(
                "error", "No real volume data for symbol: " + symbol,
                "note", "Volume Profile requires real OHLCV data with non-zero volume."
            ));
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/volume-profile", payload, symbol);
    }

    // ─────────────────────────────────────────────
    // HEALTH CHECK (Python Worker status)
    // ─────────────────────────────────────────────

    @GetMapping("/health")
    public ResponseEntity<?> checkQuantWorkerHealth() {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                QUANT_WORKER_URL + "/health", String.class
            );
            return ResponseEntity.ok(Map.of(
                "java_bridge", "UP",
                "python_quant_worker", response.getBody()
            ));
        } catch (Exception e) {
            log.error("QUANT WORKER UNREACHABLE: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                "java_bridge", "UP",
                "python_quant_worker", "DOWN",
                "error", "quant_worker.py δεν τρέχει στο port 8003"
            ));
        }
    }

    // ─────────────────────────────────────────────
    // PRIVATE HELPERS
    // ─────────────────────────────────────────────

    /**
     * Μετατρέπει τα MarketData entities σε OHLCV list για την Python.
     * Κάθε candle είναι Map με open/high/low/close/volume.
     */
    private Map<String, Object> buildOhlcvPayload(String symbol, List<MarketData> data) {
        List<Map<String, Object>> ohlcv = data.stream()
            .map(d -> Map.<String, Object>of(
                "open",   d.getOpen()   != null ? d.getOpen()   : d.getClose(),
                "high",   d.getHigh()   != null ? d.getHigh()   : d.getClose(),
                "low",    d.getLow()    != null ? d.getLow()    : d.getClose(),
                "close",  d.getClose(),
                "volume", d.getVolume() != null ? d.getVolume() : 0L
            ))
            .collect(Collectors.toList());

        return Map.of("symbol", symbol, "prices", ohlcv);
    }

    /**
     * Κοινό HTTP forwarding προς τον Python quant_worker.
     * Χτίζει το τελικό response με metadata για το Frontend.
     */
    private ResponseEntity<?> forwardToQuant(String endpoint, Map<String, Object> payload, String symbol) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(payload, headers);

        try {
            ResponseEntity<Object> pythonResponse = restTemplate.postForEntity(
                QUANT_WORKER_URL + endpoint,
                entity,
                Object.class
            );

            Map<String, Object> response = Map.of(
                "status", "SUCCESS",
                "timestamp", LocalDateTime.now().toString(),
                "symbol", symbol,
                "source", "Python Quant Engine (port 8003)",
                "data", pythonResponse.getBody()
            );

            log.info("QUANT SUCCESS → symbol: {} | endpoint: {}", symbol, endpoint);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("QUANT WORKER FAILURE → endpoint: {} | error: {}", endpoint, e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                "status", "ERROR",
                "error", "Quant Worker unreachable. Τρέχει το quant_worker.py στο port 8003;",
                "detail", e.getMessage()
            ));
        }
    }
}
