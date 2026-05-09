package com.dealership.quant_trading;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:4200")
public class MarketDataController {
    @Autowired
    private MarketDataRepository repository;
    @GetMapping("/market-data")
    public List<MarketData> getMarketData() {
        return repository.findAll();
    }
}