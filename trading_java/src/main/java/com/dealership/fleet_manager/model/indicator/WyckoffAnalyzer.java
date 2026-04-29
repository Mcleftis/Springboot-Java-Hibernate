package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class WyckoffAnalyzer {
 private final List<MarketData> data;
 public WyckoffAnalyzer(List<MarketData> data){this.data=data;}
 public String getWyckoffPhase(){
 if(data.size()<10) return "ACCUMULATION";
 double first=data.get(0).getClose();
 double last=data.get(data.size()-1).getClose();
 double mid=data.get(data.size()/2).getClose();
 if(last>first && last>mid) return "MARKUP";
 if(last<first && last<mid) return "MARKDOWN";
 if(last>first) return "ACCUMULATION";
 return "DISTRIBUTION";
 }
 public String getInstitutionalBehavior(){
 if(data.isEmpty()) return "UNKNOWN";
 double avgVol=data.stream().mapToLong(MarketData::getVolume).average().orElse(0);
 long lastVol=data.get(data.size()-1).getVolume();
 return lastVol>avgVol*1.5?"HIGH_INSTITUTIONAL_ACTIVITY":"NORMAL_ACTIVITY";
 }}