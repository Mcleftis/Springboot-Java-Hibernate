package com.dealership.quant_trading;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
import com.dealership.quant_trading.model.MarketData;

@Repository
public interface MarketDataRepository extends JpaRepository<MarketData, Long> {
    
    @Query(value = "SELECT * FROM market_data ORDER BY date DESC LIMIT 300", nativeQuery = true)
    List<MarketData> findRecentData();
}
