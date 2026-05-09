package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class HistoricalComparisonIndicator {
 private final List<MarketData> data;
 private final int lookback;
 public HistoricalComparisonIndicator(List<MarketData> data,int lookback){this.data=data;this.lookback=lookback;}
 public String getMostSimilarPeriod(){
 if(data.size()<lookback) return "INSUFFICIENT_DATA";
 MarketData oldest=data.get(0);
 MarketData newest=data.get(data.size()-1);
 double change=((newest.getClose()-oldest.getClose())/oldest.getClose())*100;
 return String.format("SIMILAR_PERIOD(change=%.1f%%)",change);
 }}