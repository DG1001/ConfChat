package com.presentai.service;

import com.presentai.model.Feedback;
import com.presentai.model.Presentation;
import com.presentai.repository.FeedbackRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class FeedbackService {

    @Autowired
    private FeedbackRepository feedbackRepository;

    public Feedback createFeedback(String content, Presentation presentation) {
        Feedback feedback = new Feedback();
        feedback.setContent(content);
        feedback.setPresentation(presentation);
        feedback.setProcessed(false);
        
        return feedbackRepository.save(feedback);
    }

    public List<Feedback> getFeedbacksByPresentation(Long presentationId) {
        return feedbackRepository.findByPresentationIdOrderByCreatedAtDesc(presentationId);
    }

    public List<Feedback> getUnprocessedFeedbacks(Long presentationId) {
        return feedbackRepository.findByPresentationIdAndIsProcessed(presentationId, false);
    }

    public void markFeedbacksAsProcessed(List<Feedback> feedbacks, String aiResponse) {
        for (Feedback feedback : feedbacks) {
            feedback.setAiResponse(aiResponse);
            feedback.setProcessed(true);
        }
        feedbackRepository.saveAll(feedbacks);
    }
}
