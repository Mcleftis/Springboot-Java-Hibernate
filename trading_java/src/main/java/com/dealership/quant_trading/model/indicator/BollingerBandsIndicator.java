package com.dealership.fleet_manager.model.indicator;
import com.dealership.fleet_manager.model.MarketData;
import java.util.List;
public class BollingerBandsIndicator {
 private final List<MarketData> data;
 private final int period;
 private final double multiplier;
 public BollingerBandsIndicator(List<MarketData> data,int period,double multiplier){this.data=data;this.period=period;this.multiplier=multiplier;}
 private double sma(){return data.stream().mapToDouble(MarketData::getClose).average().orElse(0);}
 private double std(){double avg=sma();return Math.sqrt(data.stream().mapToDouble(d->Math.pow(d.getClose()-avg,2)).average().orElse(0));}
 public Double getUpperBand(){return sma()+multiplier*std();}
 public Double getLowerBand(){return sma()-multiplier*std();}
 public String getBandSignal(){
 if(data.isEmpty()) return "NEUTRAL";
 double last=data.get(data.size()-1).getClose();
 if(last>=getUpperBand()) return "AT_UPPER_BAND";
 if(last<=getLowerBand()) return "AT_LOWER_BAND";
 return "INSIDE_BANDS";
 }}