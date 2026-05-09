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
 * QuantController â€” Bridge Î±Ï€ÏŒ Java â†’ Python quant_worker.py (port 8003).
 *
 * Î‘Î½Ï„Î¹ÎºÎ±Î¸Î¹ÏƒÏ„Î¬ Ï€Î»Î®ÏÏ‰Ï‚ Ï„Î¿Î½ AnalysisController.java.
 * Î— Java Î”Î•Î ÎºÎ¬Î½ÎµÎ¹ indicators. Î‘Ï€Î»ÏŽÏ‚:
 *  1. Î¤ÏÎ±Î²Î¬ÎµÎ¹ Ï„Î± OHLCV Î´ÎµÎ´Î¿Î¼Î­Î½Î± Î±Ï€ÏŒ Ï„Î· DB
 *  2. Î¤Î± Ï€Î±ÎºÎµÏ„Î¬ÏÎµÎ¹ ÏƒÎµ JSON
 *  3. Î¤Î± ÏƒÏ„Î­Î»Î½ÎµÎ¹ ÏƒÏ„Î·Î½ Python
 *  4. Î•Ï€Î¹ÏƒÏ„ÏÎ­Ï†ÎµÎ¹ Ï„Î¿ Î±Ï€Î¿Ï„Î­Î»ÎµÏƒÎ¼Î± ÏƒÏ„Î¿ Frontend
 */
@RestController
@org.springframework.web.bind.annotation.CrossOrigin(origins="http://localhost:4200")
@RequestMapping("/api/quant")
@RequiredArgsConstructor
public class QuantController {

    private static final Logger log = LoggerFactory.getLogger(QuantController.class);

    private static final String QUANT_WORKER_URL = "http://localhost:8003";

    private final MarketDataService marketDataService;
    private final RestTemplate restTemplate;

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // FULL ANALYSIS (RSI, MACD, ATR, Order Blocks, FVGs, Wyckoff)
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @PostMapping("/analyze/{symbol}")
    public ResponseEntity<?> analyze(@PathVariable String symbol) {
        log.info("QUANT ANALYSIS REQUEST â†’ symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/analyze", payload, symbol);
    }

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // WYCKOFF FULL (Î¼Îµ Volume, Springs, Upthrusts)
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @PostMapping("/wyckoff/{symbol}")
    public ResponseEntity<?> wyckoffFull(@PathVariable String symbol) {
        log.info("WYCKOFF ANALYSIS REQUEST â†’ symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/wyckoff-full", payload, symbol);
    }

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // ORDER BLOCKS â€” Institutional Zones
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @PostMapping("/order-blocks/{symbol}")
    public ResponseEntity<?> orderBlocks(@PathVariable String symbol) {
        log.info("ORDER BLOCKS REQUEST â†’ symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/order-blocks", payload, symbol);
    }

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // VOLUME PROFILE â€” POC, Value Area
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @PostMapping("/volume-profile/{symbol}")
    public ResponseEntity<?> volumeProfile(@PathVariable String symbol) {
        log.info("VOLUME PROFILE REQUEST â†’ symbol: {}", symbol);

        List<MarketData> data = marketDataService.getBySymbol(symbol);
        if (data.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        // Volume Profile Î‘Î Î‘Î™Î¤Î•Î™ Ï€ÏÎ±Î³Î¼Î±Ï„Î¹ÎºÏŒ volume
        boolean hasVolume = data.stream().anyMatch(d -> d.getVolume() != null && d.getVolume() > 0);
        if (!hasVolume) {
            log.warn("VOLUME PROFILE SKIPPED â€” Symbol {} has no real volume data", symbol);
            return ResponseEntity.badRequest().body(Map.of(
                "error", "No real volume data for symbol: " + symbol,
                "note", "Volume Profile requires real OHLCV data with non-zero volume."
            ));
        }

        Map<String, Object> payload = buildOhlcvPayload(symbol, data);
        return forwardToQuant("/volume-profile", payload, symbol);
    }

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // HEALTH CHECK (Python Worker status)
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
                "error", "quant_worker.py Î´ÎµÎ½ Ï„ÏÎ­Ï‡ÎµÎ¹ ÏƒÏ„Î¿ port 8003"
            ));
        }
    }

    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    // PRIVATE HELPERS
    // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    /**
     * ÎœÎµÏ„Î±Ï„ÏÎ­Ï€ÎµÎ¹ Ï„Î± MarketData entities ÏƒÎµ OHLCV list Î³Î¹Î± Ï„Î·Î½ Python.
     * ÎšÎ¬Î¸Îµ candle ÎµÎ¯Î½Î±Î¹ Map Î¼Îµ open/high/low/close/volume.
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
     * ÎšÎ¿Î¹Î½ÏŒ HTTP forwarding Ï€ÏÎ¿Ï‚ Ï„Î¿Î½ Python quant_worker.
     * Î§Ï„Î¯Î¶ÎµÎ¹ Ï„Î¿ Ï„ÎµÎ»Î¹ÎºÏŒ response Î¼Îµ metadata Î³Î¹Î± Ï„Î¿ Frontend.
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

            log.info("QUANT SUCCESS â†’ symbol: {} | endpoint: {}", symbol, endpoint);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("QUANT WORKER FAILURE â†’ endpoint: {} | error: {}", endpoint, e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                "status", "ERROR",
                "error", "Quant Worker unreachable. Î¤ÏÎ­Ï‡ÎµÎ¹ Ï„Î¿ quant_worker.py ÏƒÏ„Î¿ port 8003;",
                "detail", e.getMessage()
            ));
        }
    }
}

