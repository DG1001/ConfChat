package com.presentai.repository;

import com.presentai.model.Feedback;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FeedbackRepository extends JpaRepository<Feedback, Long> {
    List<Feedback> findByPresentationId(Long presentationId);
    List<Feedback> findByPresentationIdAndIsProcessed(Long presentationId, boolean isProcessed);
    List<Feedback> findByPresentationIdOrderByCreatedAtDesc(Long presentationId);
}
