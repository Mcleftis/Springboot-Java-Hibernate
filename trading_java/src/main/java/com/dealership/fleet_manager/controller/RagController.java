package com.dealership.fleet_manager.controller;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/rag") // Το endpoint που χτυπάει το Frontend σου
public class RagController {

    // Ενσωματωμένος Enterprise Logger
    private static final Logger auditLogger = LoggerFactory.getLogger(RagController.class);
    
    // ΕΔΩ ΕΙΝΑΙ ΤΟ ΚΑΛΩΔΙΟ: Η διεύθυνση του Python Server
    private final String PYTHON_RAG_URL = "http://localhost:8002/ask";
    
    // In-Memory Rate Limiter
    private final Map<String, Integer> requestCounts = new ConcurrentHashMap<>();
    private final int MAX_REQUESTS = 5; // 5 ερωτήσεις max για προστασία

    @PostMapping("/ask")
    public ResponseEntity<?> askRagWorker(@RequestBody Map<String, String> request) {
        String userId = request.getOrDefault("userId", "anonymous_user"); //
        String question = request.get("question"); //

        // --- 1. RATE LIMITING (Προστασία Server) ---
        int currentRequests = requestCounts.getOrDefault(userId, 0); //[cite: 2]
        if (currentRequests >= MAX_REQUESTS) { //[cite: 2]
            auditLogger.warn("SECURITY ALERT: User {} exceeded rate limit!", userId); //[cite: 2]
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS) //[cite: 2]
                .body(Map.of("error", "Rate limit exceeded. Παρακαλώ περιμένετε.")); //[cite: 2]
        }
        requestCounts.put(userId, currentRequests + 1); //[cite: 2]

        // Προετοιμασία του HTTP Request προς την Python[cite: 2]
        RestTemplate restTemplate = new RestTemplate(); //[cite: 2]
        HttpHeaders headers = new HttpHeaders(); //[cite: 2]
        headers.setContentType(MediaType.APPLICATION_JSON); //[cite: 2]
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(request, headers); //[cite: 2]

        try {
            // Κλήση στο αυτόνομο Python Microservice[cite: 2]
            ResponseEntity<String> pythonResponse = restTemplate.postForEntity(PYTHON_RAG_URL, entity, String.class); //[cite: 2]
            
            // --- 2. DATA TRANSFORMATION (Αλλαγή Format) ---
            ObjectMapper mapper = new ObjectMapper(); //[cite: 2]
            JsonNode root = mapper.readTree(pythonResponse.getBody()); // Διαβάζει το JSON της Python[cite: 2]
            String rawAnswer = root.path("result").asText(); // Τραβάει το "result"[cite: 2]

            // Φτιάχνει το όμορφο τελικό JSON για το Frontend[cite: 2]
            Map<String, Object> transformedResponse = Map.of(
                "status", "SUCCESS", //[cite: 2]
                "timestamp", LocalDateTime.now().toString(), //[cite: 2]
                "data", Map.of( //[cite: 2]
                    "answer", rawAnswer, //[cite: 2]
                    "source", "Secure RAG Enterprise Worker" //[cite: 2]
                )
            );

            // --- 3. AUDIT LOGGING ---
            auditLogger.info("AUDIT LOG -> User: '{}' | Question: '{}' | System Replied Successfully.", userId, question); //[cite: 2]

            return ResponseEntity.ok(transformedResponse); //[cite: 2]

        } catch (Exception e) { //[cite: 2]
            auditLogger.error("SYSTEM ERROR -> RAG Worker Failure: {}", e.getMessage()); //[cite: 2]
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR) //[cite: 2]
                .body(Map.of("error", "AI Bridge Failure. Ελέγξτε αν τρέχει η Python στην 8002.")); //[cite: 2]
        }
    }
}