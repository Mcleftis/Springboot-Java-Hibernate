package com.dealership.fleet_manager.service;
import com.dealership.fleet_manager.model.AnalysisResult;
import com.dealership.fleet_manager.model.MarketData;
import com.dealership.fleet_manager.model.indicator.*;
import com.dealership.fleet_manager.repository.AnalysisResultRepository;
import com.dealership.fleet_manager.repository.MarketDataRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
@Slf4j
@Service
@RequiredArgsConstructor
public class AnalysisService {
    private final MarketDataRepository marketDataRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final PythonAnalysisClient pythonClient;
    public AnalysisResult analyze(String symbol) {
        List<MarketData> data = marketDataRepository.findBySymbolOrderByDateAsc(symbol);
        if (data.isEmpty()) { throw new RuntimeException("No data found for: " + symbol); }
        RSIIndicator rsi = new RSIIndicator(data, 14);
        WyckoffAnalyzer wyckoff = new WyckoffAnalyzer(data);
        VolumeDeltaIndicator delta = new VolumeDeltaIndicator(data, 20);
        MACDIndicator macd = new MACDIndicator(data);
        BollingerBandsIndicator bollinger = new BollingerBandsIndicator(data, 20, 2.0);
        HistoricalComparisonIndicator historical = new HistoricalComparisonIndicator(data, 30);
        Double rsiValue = rsi.calculate();
        String wyckoffPhase = wyckoff.getWyckoffPhase();
        String institutionalBehavior = wyckoff.getInstitutionalBehavior();
        String deltaPressure = delta.getInstitutionalPressure();
        String macdSignal = macd.getSignalLine();
        String bollingerSignal = bollinger.getBandSignal();
        Double upperBand = bollinger.getUpperBand();
        Double lowerBand = bollinger.getLowerBand();
        String historicalMatch = historical.getMostSimilarPeriod();
        List<Double> prices = data.stream().map(MarketData::getClose).collect(Collectors.toList());
        String aiAnalysis = pythonClient.getAIAnalysis(symbol, prices);
        log.info("Symbol: {} | RSI: {} | Wyckoff: {} | Delta: {} | MACD: {} | Bollinger: {} | Historical: {} | AI: {}", symbol, rsiValue, wyckoffPhase, deltaPressure, macdSignal, bollingerSignal, historicalMatch, aiAnalysis);
        double support = data.stream().mapToDouble(MarketData::getLow).min().orElse(0);
        double resistance = data.stream().mapToDouble(MarketData::getHigh).max().orElse(0);
        AnalysisResult result = new AnalysisResult();
        result.setSymbol(symbol);
        result.setSupportZone(support);
        result.setResistanceZone(resistance);
        result.setRiskLevel(rsiValue != null ? rsiValue / 100 : 0.0);
        try { result.setCyclePhase(AnalysisResult.CyclePhase.valueOf(wyckoffPhase)); } catch(Exception e) {}
        if (rsiValue != null) {
            if (rsiValue > 70) {
                result.setCondition(AnalysisResult.MarketCondition.OVERBOUGHT);
                result.setRecommendation("OVERBOUGHT | " + institutionalBehavior + " | Delta: " + deltaPressure + " | MACD: " + macdSignal + " | Bollinger: " + bollingerSignal + " | Upper Band: " + upperBand + " | Lower Band: " + lowerBand + " | Historical: " + historicalMatch + " | " + aiAnalysis + " | Possible sell zone: " + resistance);
            } else if (rsiValue < 30) {
                result.setCondition(AnalysisResult.MarketCondition.OVERSOLD);
                result.setRecommendation("OVERSOLD | " + institutionalBehavior + " | Delta: " + deltaPressure + " | MACD: " + macdSignal + " | Bollinger: " + bollingerSignal + " | Upper Band: " + upperBand + " | Lower Band: " + lowerBand + " | Historical: " + historicalMatch + " | " + aiAnalysis + " | Possible buy zone: " + support);
            } else {
                result.setCondition(AnalysisResult.MarketCondition.NEUTRAL);
                result.setRecommendation("NEUTRAL | " + institutionalBehavior + " | Delta: " + deltaPressure + " | MACD: " + macdSignal + " | Bollinger: " + bollingerSignal + " | Upper Band: " + upperBand + " | Lower Band: " + lowerBand + " | Historical: " + historicalMatch + " | " + aiAnalysis);
            }
        }
        return analysisResultRepository.save(result);
    }
    public Optional<AnalysisResult> getLatestAnalysis(String symbol) {
        return analysisResultRepository.findTopBySymbolOrderByAnalyzedAtDesc(symbol);
    }
}
