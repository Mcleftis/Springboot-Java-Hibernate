package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class MACDIndicator {
 private final List<MarketData> data;
 public MACDIndicator(List<MarketData> data){this.data=data;}
 private double ema(int period){
 if(data.isEmpty()) return 0;
 double k=2.0/(period+1);
 double ema=data.get(0).getClose();
 for(int i=1;i<data.size();i++) ema=data.get(i).getClose()*k+ema*(1-k);
 return ema;
 }
 public String getSignalLine(){
 double macd=ema(12)-ema(26);
 if(macd>0) return "BULLISH(macd="+String.format("%.2f",macd)+")";
 return "BEARISH(macd="+String.format("%.2f",macd)+")";
 }}