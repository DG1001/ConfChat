package com.presentai.model;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Data
public class Presentation {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String title;
    
    @Column(length = 1000)
    private String description;
    
    @Column(length = 2000)
    private String context;
    
    @Column(length = 10000)
    private String content;
    
    @Column(unique = true)
    private String accessCode;
    
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User creator;
    
    @OneToMany(mappedBy = "presentation", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Feedback> feedbacks = new ArrayList<>();
    
    @Column(length = 10000)
    private String cachedAiContent;
    
    private LocalDateTime lastUpdated;
    
    private boolean processingScheduled;
    
    private LocalDateTime nextProcessingTime;
}
