package com.dealership.quant_trading;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import jakarta.annotation.PostConstruct;
import java.io.BufferedReader;
import java.io.FileReader;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
@Component
public class CsvBatchIngestor {
    private final JdbcTemplate jdbcTemplate;
    public CsvBatchIngestor(JdbcTemplate jdbcTemplate) { this.jdbcTemplate = jdbcTemplate; }
    @PostConstruct
    public void ingest() {
        String sql = "INSERT INTO market_data (record_date, close) VALUES (?, ?)";
        List<Object[]> batchArgs = new ArrayList<>();
        DateTimeFormatter f = DateTimeFormatter.ofPattern("M/d/yyyy");
        try (BufferedReader br = new BufferedReader(new FileReader("Daily.csv"))) {
            String line;
            br.readLine();
            while ((line = br.readLine()) != null) {
                String[] v = line.split(",");
                if (v.length < 2) continue;
                LocalDate d;
                try {
                    d = LocalDate.parse(v[0]);
                } catch (Exception ex) {
                    try {
                        d = LocalDate.parse(v[0], f);
                    } catch (Exception e2) {
                        continue;
                    }
                }
                Double p;
                try {
                    p = Double.parseDouble(v[1]);
                } catch (Exception ex) {
                    continue;
                }
                batchArgs.add(new Object[]{d, p});
                if (batchArgs.size() == 1000) {
                    jdbcTemplate.batchUpdate(sql, batchArgs);
                    batchArgs.clear();
                }
            }
            if (!batchArgs.isEmpty()) {
                jdbcTemplate.batchUpdate(sql, batchArgs);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}