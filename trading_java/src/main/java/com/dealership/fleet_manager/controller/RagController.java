package com.dealership.fleet_manager.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.Map;

@RestController
@RequestMapping("/api/rag")
public class RagController {

    private final String PYTHON_RAG_URL = "http://localhost:8002/ask";

    @PostMapping("/ask")
    public ResponseEntity<String> askRagWorker(@RequestBody Map<String, String> request) {
        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        // Φτιάχνει το πακέτο και το στέλνει στην Python
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request, headers);
        
        try {
            return restTemplate.postForEntity(PYTHON_RAG_URL, entity, String.class);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("{\"error\": \"Ο Python RAG Worker δεν απαντάει. Είναι ανοιχτός στην 8002?\"}");
        }
    }
}
