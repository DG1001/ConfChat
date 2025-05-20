package com.presentai.repository;

import com.presentai.model.Presentation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PresentationRepository extends JpaRepository<Presentation, Long> {
    List<Presentation> findByCreatorId(Long userId);
    Optional<Presentation> findByAccessCode(String accessCode);
}
