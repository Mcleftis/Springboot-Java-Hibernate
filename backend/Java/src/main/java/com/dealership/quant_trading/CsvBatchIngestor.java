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

    private static final String[] CURRENCIES = {
        "USD", "EUR", "JPY", "GBP", "CAD", "CHF", "INR", "CNY", "TRY", "SAR",
        "IDR", "AED", "THB", "VND", "EGP", "KRW", "RUB", "ZAR", "AUD"
    };

    public CsvBatchIngestor(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @PostConstruct
    public void ingest() {
        Storage storage = StorageOptions.getDefaultInstance().getService();

        String sql = "INSERT INTO market_data (symbol, date, open, high, low, \"close\", volume, daily_return, range) "
                   + "VALUES (?, ?, 0.0, 0.0, 0.0, ?, 0, 0.0, 0.0) "
                   + "ON CONFLICT (symbol, date) DO NOTHING";

        DateTimeFormatter f = DateTimeFormatter.ofPattern("M/d/yyyy");

        for (String fileName : FILES) {
            try {
                Blob blob = storage.get(BUCKET, fileName);
                if (blob == null) continue;

                List<Object[]> batchArgs = new ArrayList<>();

                try (BufferedReader br = new BufferedReader(new InputStreamReader(Channels.newInputStream(blob.reader())))) {
                    String header = br.readLine();
                    if (header == null) continue;

                    String suffix = fileName.replace(".csv", "");
                    String line;

                    while ((line = br.readLine()) != null) {
                        String[] v = line.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)");
                        if (v.length < 2) continue;

                        LocalDate d;
                        try {
                            d = LocalDate.parse(v[0].trim());
                        } catch (Exception e) {
                            try { d = LocalDate.parse(v[0].trim(), f); }
                            catch (Exception e2) { continue; }
                        }

                        for (int i = 0; i < CURRENCIES.length; i++) {
                            int col = i + 1;
                            if (col >= v.length) break;
                            String raw = v[col].trim().replace(",", "").replace("\"", "");
                            if (raw.isEmpty() || raw.equals("#N/A")) continue;
                            double p;
                            try { p = Double.parseDouble(raw); } catch (Exception e) { continue; }
                            String symbol = "GOLD_" + CURRENCIES[i] + "_" + suffix;
                            batchArgs.add(new Object[]{symbol, d, p});
                        }

                        if (batchArgs.size() >= 1000) {
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
                System.err.println("Error: " + e.getMessage());
            }
        }
    }
}
