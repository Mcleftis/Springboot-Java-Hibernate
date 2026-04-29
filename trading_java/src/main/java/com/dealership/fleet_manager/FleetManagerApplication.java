package com.dealership.fleet_manager;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;
@SpringBootApplication
public class FleetManagerApplication {
    public static void main(String[] args) { SpringApplication.run(FleetManagerApplication.class, args); }
    @Bean
    public RestTemplate restTemplate() { return new RestTemplate(); }
}
