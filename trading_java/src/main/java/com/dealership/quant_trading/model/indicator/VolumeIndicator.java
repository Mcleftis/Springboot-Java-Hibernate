package com.dealership.fleet_manager.model.indicator;

import com.dealership.fleet_manager.model.MarketData;
import java.util.List;

public class VolumeIndicator extends Indicator {

    public VolumeIndicator(List<MarketData> data) {
        super("VOLUME_DELTA", data);
    }

    @Override
    public Double calculate() {
        if (data.size() < 20) return null;

        List<MarketData> recent = data.subList(data.size() - 20, data.size());
        double avgVolume = recent.stream()
                .mapToLong(MarketData::getVolume)
                .average()
                .orElse(0);

        long lastVolume = data.get(data.size() - 1).getVolume();
        return ((double) lastVolume / avgVolume) * 100;
    }

    @Override
    protected String interpretValue(Double value) {
        if (value > 150) return "HIGH_VOLUME";    // Institutional activity
        if (value < 50)  return "LOW_VOLUME"; 
        return "NORMAL_VOLUME";
    }
}