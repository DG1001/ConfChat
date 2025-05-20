package com.presentai.scheduler;

import com.presentai.model.Feedback;
import com.presentai.model.Presentation;
import com.presentai.repository.PresentationRepository;
import com.presentai.service.AiService;
import com.presentai.service.FeedbackService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

@Component
public class FeedbackProcessor {

    @Autowired
    private PresentationRepository presentationRepository;

    @Autowired
    private FeedbackService feedbackService;

    @Autowired
    private AiService aiService;

    @Scheduled(fixedRate = 10000) // Alle 10 Sekunden prüfen
    public void processFeedbackQueue() {
        LocalDateTime now = LocalDateTime.now();
        
        // Präsentationen finden, die verarbeitet werden müssen
        List<Presentation> presentationsToProcess = presentationRepository.findAll().stream()
                .filter(p -> p.isProcessingScheduled() && p.getNextProcessingTime() != null && p.getNextProcessingTime().isBefore(now))
                .toList();
        
        for (Presentation presentation : presentationsToProcess) {
            try {
                // Alle Feedbacks abrufen
                List<Feedback> allFeedbacks = feedbackService.getFeedbacksByPresentation(presentation.getId());
                
                // KI-Antwort mit allen Feedbacks generieren
                String aiResponse = aiService.generateAiContent(presentation.getContext(), presentation.getContent(), allFeedbacks);
                
                // Unverarbeitete Feedbacks aktualisieren
                List<Feedback> unprocessedFeedbacks = feedbackService.getUnprocessedFeedbacks(presentation.getId());
                feedbackService.markFeedbacksAsProcessed(unprocessedFeedbacks, aiResponse);
                
                // Präsentations-Cache aktualisieren
                presentation.setCachedAiContent(aiResponse);
                presentation.setLastUpdated(LocalDateTime.now());
                presentation.setProcessingScheduled(false);
                presentation.setNextProcessingTime(null);
                
                presentationRepository.save(presentation);
            } catch (Exception e) {
                e.printStackTrace();
                // Bei Fehler aus der Warteschlange entfernen
                presentation.setProcessingScheduled(false);
                presentationRepository.save(presentation);
            }
        }
    }
}
