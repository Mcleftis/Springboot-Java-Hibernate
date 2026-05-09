package com.dealership.fleet_manager.repository;

import com.dealership.fleet_manager.model.MarketData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.time.LocalDate;
import java.util.List;

@Repository
public interface MarketDataRepository extends JpaRepository<MarketData, Long> {

    List<MarketData> findBySymbolOrderByDateAsc(String symbol);

    List<MarketData> findBySymbolAndDateBetweenOrderByDateAsc(
        String symbol, LocalDate from, LocalDate to
    );

    @Query("SELECT m FROM MarketData m WHERE m.symbol = :symbol ORDER BY m.date DESC LIMIT :limit")
    List<MarketData> findLatestBySymbol(String symbol, int limit);

    boolean existsBySymbolAndDate(String symbol, LocalDate date);
}