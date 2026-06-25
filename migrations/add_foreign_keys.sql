ALTER TABLE market_data
  ADD CONSTRAINT uq_market_data_symbol_date UNIQUE (symbol, date);

ALTER TABLE analysis_results
  ADD COLUMN IF NOT EXISTS market_data_id BIGINT;

UPDATE analysis_results ar
SET market_data_id = md.id
FROM market_data md
WHERE ar.symbol = md.symbol
  AND ar.market_data_id IS NULL
  AND md.date = (
    SELECT MAX(md2.date)
    FROM market_data md2
    WHERE md2.symbol = ar.symbol
      AND md2.date <= CAST(ar.analyzed_at AS DATE)
  );

ALTER TABLE analysis_results
  ADD CONSTRAINT fk_analysis_market_data
  FOREIGN KEY (market_data_id)
  REFERENCES market_data (id)
  ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_analysis_market_data_id
  ON analysis_results (market_data_id);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol_date
  ON market_data (symbol, date);
