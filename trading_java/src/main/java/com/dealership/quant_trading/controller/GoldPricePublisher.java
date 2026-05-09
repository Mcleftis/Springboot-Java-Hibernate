package com.dealership.fleet_manager.controller;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class GoldPricePublisher {
    @Autowired
    private RabbitTemplate rabbitTemplate;

    public void sendPriceToQueue(String priceDataJson) {
        rabbitTemplate.convertAndSend("gold_prices_queue", priceDataJson);
    }
}
