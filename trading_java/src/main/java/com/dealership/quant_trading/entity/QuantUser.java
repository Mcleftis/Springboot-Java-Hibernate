package com.dealership.fleet_manager.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "quant_users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class QuantUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String email;
    private String password;
    
    private boolean hasActiveSubscription;
    private LocalDateTime subscriptionEndDate;

}