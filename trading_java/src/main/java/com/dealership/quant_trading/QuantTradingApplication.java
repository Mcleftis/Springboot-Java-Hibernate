package com.dealership.quant_trading;
// Δηλώνουμε σε ποιο πακέτο ανήκει αυτή η κλάση.
// Είναι απλώς η “διεύθυνση” του αρχείου μέσα στο project.

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
// Αυτές οι δύο import φέρνουν τα εργαλεία της Spring Boot
// που επιτρέπουν στην εφαρμογή να ξεκινήσει.

@SpringBootApplication
// Αυτός ο σχολιασμός λέει στη Spring:
// “Αυτή είναι η βασική εφαρμογή. Ξεκίνα από εδώ.”
// Περιλαμβάνει:
// - @Configuration (ρυθμίσεις)
// - @EnableAutoConfiguration (αυτόματες ρυθμίσεις)
// - @ComponentScan (βρες όλα τα components στο project)

public class QuantTradingApplication {

    public static void main(String[] args) {
        // Αυτή είναι η πρώτη μέθοδος που τρέχει όταν ξεκινάει το πρόγραμμα.
        // Είναι το σημείο εκκίνησης της εφαρμογής.

        SpringApplication.run(QuantTradingApplication.class, args);
        // Εδώ λέμε στη Spring Boot:
        // “Ξεκίνα την εφαρμογή, φόρτωσε όλα τα components,
        //  άνοιξε τα REST endpoints, σύνδεσε τη βάση,
        //  και κάνε ό,τι χρειάζεται για να λειτουργήσει το σύστημα.”
    }

}
