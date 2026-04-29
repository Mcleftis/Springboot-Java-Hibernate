package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class RSIIndicator {
 private final List<MarketData> data;
 private final int period;
 public RSIIndicator(List<MarketData> data, int period){this.data=data;this.period=period;}
 public Double calculate(){
 if(data.size()<period+1) return 50.0;
 double gains=0,losses=0;
 for(int i=data.size()-period;i<data.size();i++){
 double change=data.get(i).getClose()-data.get(i-1).getClose();
 if(change>0) gains+=change; else losses+=Math.abs(change);
 }
 if(losses==0) return 100.0;
 double rs=gains/losses;
 return 100-(100/(1+rs));
 }}