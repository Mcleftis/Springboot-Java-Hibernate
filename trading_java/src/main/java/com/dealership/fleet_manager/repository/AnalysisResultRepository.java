package com.dealership.fleet_manager.repository;

import com.dealership.fleet_manager.model.AnalysisResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface AnalysisResultRepository extends JpaRepository<AnalysisResult, Long> {

    List<AnalysisResult> findBySymbolOrderByAnalyzedAtDesc(String symbol);

    Optional<AnalysisResult> findTopBySymbolOrderByAnalyzedAtDesc(String symbol);
}