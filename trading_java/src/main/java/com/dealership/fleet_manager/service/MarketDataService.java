package com.dealership.fleet_manager.service;

import com.dealership.fleet_manager.model.MarketData;
import com.dealership.fleet_manager.repository.MarketDataRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class MarketDataService {

    private final MarketDataRepository marketDataRepository;

    public List<MarketData> importFromCsv(MultipartFile file, String symbol) throws Exception {
        List<MarketData> results = new ArrayList<>();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream()));
             CSVParser csvParser = new CSVParser(reader,
                CSVFormat.DEFAULT.withFirstRecordAsHeader().withTrim())) {

            for (CSVRecord record : csvParser) {
                LocalDate date = LocalDate.parse(
                    record.get("Date"),
                    DateTimeFormatter.ofPattern("M/d/yyyy")
                );

                String usdValue = record.get("USD");
                if (usdValue == null || usdValue.equals("#N/A")) continue;

                double price = Double.parseDouble(usdValue.replace(",", ""));
                MarketData data = new MarketData();
                data.setSymbol(symbol);
                data.setDate(date);
                data.setOpen(price);
                data.setHigh(price);
                data.setLow(price);
                data.setClose(price);
                data.setVolume(0L);
                results.add(data);
            }
        }

        List<MarketData> saved = marketDataRepository.saveAll(results);
        log.info("Imported {} records for symbol {}", saved.size(), symbol);
        return saved;
    }

    public List<MarketData> getBySymbol(String symbol) {
        return marketDataRepository.findBySymbolOrderByDateAsc(symbol);
    }

    public List<MarketData> getLatest(String symbol, int limit) {
        return marketDataRepository.findLatestBySymbol(symbol, limit);
    }
}