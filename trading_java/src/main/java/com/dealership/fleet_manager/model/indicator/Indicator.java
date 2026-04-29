package com.dealership.fleet_manager.model.indicator;

import com.dealership.fleet_manager.model.MarketData;
import java.util.List;

public abstract class Indicator {

    protected String name;
    protected List<MarketData> data;

    public Indicator(String name, List<MarketData> data) {
        this.name = name;
        this.data = data;
    }

    public abstract Double calculate();

    public String getSignal() {
        Double value = calculate();
        if (value == null) return "NO_SIGNAL";
        return interpretValue(value);
    }

    protected abstract String interpretValue(Double value);

    public String getName() { return name; }
}