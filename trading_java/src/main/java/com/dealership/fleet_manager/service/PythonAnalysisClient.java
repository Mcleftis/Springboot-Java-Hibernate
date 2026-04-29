package com.dealership.fleet_manager.service;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.List;
import java.util.Map;
@Slf4j
@Service
@RequiredArgsConstructor
public class PythonAnalysisClient {
    private final RestTemplate restTemplate;
    private static final String PYTHON_URL = "http://fleet-python:8000/analyze";
    public String getAIAnalysis(String symbol, List<Double> prices) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = Map.of("symbol", symbol, "prices", prices);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(PYTHON_URL, request, Map.class);
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map result = response.getBody();
                return String.format("AI: Predicted=%.2f | Trend=%s | Confidence=%.2f | CyclePos=%.2f | %s", ((Number) result.get("predicted_next_price")).doubleValue(), result.get("trend"), ((Number) result.get("confidence")).doubleValue(), ((Number) result.get("cycle_position")).doubleValue(), result.get("recommendation"));
            }
        } catch (Exception e) { log.warn("Python service unavailable: {}", e.getMessage()); }
        return "AI: unavailable";
    }
}
