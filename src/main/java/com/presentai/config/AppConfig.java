package com.presentai.config;

import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.security.SecureRandom;
import java.util.Random;

@Configuration
public class AppConfig {

    @Value("${registration.password:}")
    private String registrationPassword;

    @Bean
    public String registrationPassword() {
        if (registrationPassword == null || registrationPassword.isEmpty()) {
            // Generiere ein zufälliges Passwort, wenn keines gesetzt ist
            String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
            StringBuilder password = new StringBuilder();
            Random random = new SecureRandom();
            for (int i = 0; i < 12; i++) {
                password.append(chars.charAt(random.nextInt(chars.length())));
            }
            String generatedPassword = password.toString();
            System.out.println("\n\n*** WICHTIG: Generiertes Registrierungspasswort: " + generatedPassword + " ***\n\n");
            return generatedPassword;
        }
        return registrationPassword;
    }

    @Bean
    public Parser markdownParser() {
        return Parser.builder().build();
    }

    @Bean
    public HtmlRenderer htmlRenderer() {
        return HtmlRenderer.builder().build();
    }
}
