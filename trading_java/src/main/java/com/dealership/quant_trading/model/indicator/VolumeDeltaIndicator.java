package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class VolumeDeltaIndicator {
 private final List<MarketData> data;
 private final int period;
 public VolumeDeltaIndicator(List<MarketData> data,int period){this.data=data;this.period=period;}
 public String getInstitutionalPressure(){
 if(data.size()<2) return "NEUTRAL";
 MarketData last=data.get(data.size()-1);
 if(last.getClose()>last.getOpen()) return "BUYING_PRESSURE";
 if(last.getClose()<last.getOpen()) return "SELLING_PRESSURE";
 return "NEUTRAL";
 }}