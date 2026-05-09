package com.dealership.quant_trading;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface MarketDataRepository extends JpaRepository<MarketData, Long> {
    
    // ΑΥΤΟ ΕΙΝΑΙ ΤΟ ΚΛΕΙΔΙ: Φέρνει 300 μέρες, ούτε 10 (που βγάζει ίσια γραμμή), ούτε 72.000 (που κρασάρει)
    @Query(value = "SELECT * FROM market_data ORDER BY record_date DESC LIMIT 300", nativeQuery = true)
    List<MarketData> findRecentData();
}