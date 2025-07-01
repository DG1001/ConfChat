package com.presentai.service;

import com.presentai.model.Feedback;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiService {

    @Value("${openai.api.key:your-api-key}")
    private String apiKey;

    private final RestTemplate restTemplate = new RestTemplate();

    public String generateAiContent(String context, String content, List<Feedback> feedbacks) {
        try {
            String prompt = buildPrompt(context, content, feedbacks);
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Authorization", "Bearer " + apiKey);
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "gpt-4.1-nano");
            
            Map<String, Object> systemMessage = new HashMap<>();
            systemMessage.put("role", "system");
            systemMessage.put("content", "Du bist ein Experte für die Erstellung von informativen und gut strukturierten Präsentationsinhalten im Markdown-Format. Verwende Markdown-Formatierung für eine klare Struktur mit Überschriften, Listen, Hervorhebungen und anderen Elementen.");
            
            Map<String, Object> userMessage = new HashMap<>();
            userMessage.put("role", "user");
            userMessage.put("content", prompt);
            
            requestBody.put("messages", List.of(systemMessage, userMessage));
            requestBody.put("max_tokens", 1500);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            Map<String, Object> response = restTemplate.postForObject(
                    "https://api.openai.com/v1/chat/completions",
                    request,
                    Map.class
            );
            
            if (response != null) {
                List<Map<String, Object>> choices = (List<Map<String, Object>>) response.get("choices");
                Map<String, Object> choice = choices.get(0);
                Map<String, Object> message = (Map<String, Object>) choice.get("message");
                return (String) message.get("content");
            }
            
            return "## Fehler\nEs ist ein Fehler bei der Generierung des KI-Inhalts aufgetreten.";
        } catch (Exception e) {
            e.printStackTrace();
            return "## Fehler\nEs ist ein Fehler bei der Generierung des KI-Inhalts aufgetreten: " + e.getMessage();
        }
    }

    private String buildPrompt(String context, String content, List<Feedback> feedbacks) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("""
                Erstelle eine gut strukturierte Infoseite im Markdown-Format basierend auf dem Kontext und Hauptinhalt der Präsentation.
                
                # Kontext der Präsentation
                """).append(context).append("\n\n");
        
        prompt.append("# Hauptinhalt der Präsentation\n").append(content);
        
        if (feedbacks != null && !feedbacks.isEmpty()) {
            prompt.append("\n\n# Feedback und Fragen der Zuhörer\n");
            for (Feedback feedback : feedbacks) {
                prompt.append("- ").append(feedback.getContent()).append("\n");
            }
            
            prompt.append("\nBitte verarbeite alle Feedbacks und Fragen der Zuhörer und integriere sie sinnvoll in die Infoseite. Strukturiere die Seite mit Markdown-Überschriften, Listen und anderen Formatierungen für eine übersichtliche Darstellung.");
        }
        
        return prompt.toString();
    }
}
