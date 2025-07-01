package com.presentai;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class PresentAiApplication {

    public static void main(String[] args) {
        SpringApplication.run(PresentAiApplication.class, args);
    }
}
