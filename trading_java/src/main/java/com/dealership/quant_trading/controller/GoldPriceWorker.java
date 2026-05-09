package com.dealership.fleet_manager.controller;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

@Service
public class GoldPriceWorker {
    @RabbitListener(queues = "gold_prices_queue")
    public void processGoldPrice(String priceDataJson) {
        System.out.println("🔥 ΕΛΗΦΘΗ ΑΠΟ ΤΗΝ ΟΥΡΑ: " + priceDataJson);
    }
}
