package com.dealership.fleet_manager.controller;
import com.dealership.fleet_manager.model.AnalysisResult;
import com.dealership.fleet_manager.service.AnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
public class AnalysisController {
 private final AnalysisService analysisService;
 @PostMapping("/{symbol}")
 public ResponseEntity<AnalysisResult> analyze(@PathVariable String symbol){
 return ResponseEntity.ok(analysisService.analyze(symbol));
 }
 @GetMapping("/{symbol}")
 public ResponseEntity<AnalysisResult> getLatest(@PathVariable String symbol){
 return analysisService.getLatestAnalysis(symbol).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
 }}