package com.dealership.quant_trading;

import com.google.cloud.storage.Blob;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import jakarta.annotation.PostConstruct;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.channels.Channels;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Component
public class CsvBatchIngestor {

    private final JdbcTemplate jdbcTemplate;
    private static final String BUCKET = "quant-trading-data-strong-minutia";
    private static final String[] FILES = {
        "Daily.csv", "Monthly_Avg.csv", "Monthly_EoP.csv",
        "Quarterly_Avg.csv", "Quarterly_EoP.csv", "Weekly_EoP.csv",
        "Yearly_Avg.csv", "Yearly_EoP.csv"
    };

    public CsvBatchIngestor(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void ingest() {
        Storage storage = StorageOptions.getDefaultInstance().getService();
        String sql = "INSERT INTO market_data (record_date, \"close\") VALUES (?, ?)";
        DateTimeFormatter f = DateTimeFormatter.ofPattern("M/d/yyyy");

        for (String fileName : FILES) {
            try {
                Blob blob = storage.get(BUCKET, fileName);
                if (blob == null) {
                    System.out.println("File not found in GCS: " + fileName);
                    continue;
                }

                List<Object[]> batchArgs = new ArrayList<>();
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(Channels.newInputStream(blob.reader())))) {
                    br.readLine();
                    String line;
                    while ((line = br.readLine()) != null) {
                        String[] v = line.split(",");
                        if (v.length < 2) continue;
                        LocalDate d;
                        try {
                            d = LocalDate.parse(v[0].trim());
                        } catch (Exception ex) {
                            try {
                                d = LocalDate.parse(v[0].trim(), f);
                            } catch (Exception e2) {
                                continue;
                            }
                        }
                        double p;
                        try {
                            p = Double.parseDouble(v[1].trim().replace(",", "").replace("\"", ""));
                        } catch (Exception ex) {
                            continue;
                        }
                        batchArgs.add(new Object[]{d, p});
                        if (batchArgs.size() == 1000) {
                            jdbcTemplate.batchUpdate(sql, batchArgs);
                            batchArgs.clear();
                        }
                    }
                }
                if (!batchArgs.isEmpty()) {
                    jdbcTemplate.batchUpdate(sql, batchArgs);
                }
                System.out.println("Ingested: " + fileName);
            } catch (Exception e) {
                System.err.println("Error ingesting " + fileName + ": " + e.getMessage());
            }
        }
    }
}
