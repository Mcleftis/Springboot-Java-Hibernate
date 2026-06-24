package com.dealership.quant_trading.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/rag")
@CrossOrigin(origins = "http://localhost:4200")
public class RagController {

    private final String PYTHON_RAG_URL = "http://localhost:8002/ask";

    @PostMapping("/ask")
    public ResponseEntity<Map<String, Object>> askRag(@RequestBody Map<String, String> payload) {
        String question = payload.get("question");
        RestTemplate restTemplate = new RestTemplate();
        
        try {
            Map<String, String> pythonPayload = new HashMap<>();
            pythonPayload.put("question", question);
            
            // Η Python επιστρέφει: {"result": "..."}
            Map response = restTemplate.postForObject(PYTHON_RAG_URL, pythonPayload, Map.class);
            
            Map<String, Object> finalRes = new HashMap<>();
            finalRes.put("data", Map.of("answer", response.get("result")));
            return ResponseEntity.ok(finalRes);
        } catch (Exception e) {
            Map<String, Object> errorRes = new HashMap<>();
            errorRes.put("data", Map.of("answer", "Σφάλμα επικοινωνίας: Ο Python RAG Worker στο 8002 δεν απαντάει."));
            return ResponseEntity.status(500).body(errorRes);
        }
    }
}
