package com.presentai.service;

import com.presentai.model.Feedback;
import com.presentai.model.Presentation;
import com.presentai.model.User;
import com.presentai.repository.FeedbackRepository;
import com.presentai.repository.PresentationRepository;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.List;
import java.util.UUID;

@Service
public class PresentationService {

    @Autowired
    private PresentationRepository presentationRepository;

    @Autowired
    private FeedbackRepository feedbackRepository;

    @Autowired
    private AiService aiService;

    public List<Presentation> getPresentationsByUser(User user) {
        return presentationRepository.findByCreatorId(user.getId());
    }

    public Presentation createPresentation(String title, String description, String context, String content, User creator) {
        Presentation presentation = new Presentation();
        presentation.setTitle(title);
        presentation.setDescription(description);
        presentation.setContext(context);
        presentation.setContent(content);
        presentation.setAccessCode(UUID.randomUUID().toString().substring(0, 8));
        presentation.setCreator(creator);
        
        return presentationRepository.save(presentation);
    }

    public Presentation getPresentation(Long id) {
        return presentationRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Präsentation nicht gefunden"));
    }

    public Presentation getPresentationByAccessCode(String accessCode) {
        return presentationRepository.findByAccessCode(accessCode)
                .orElseThrow(() -> new IllegalArgumentException("Präsentation nicht gefunden"));
    }

    public void updatePresentation(Long id, String title, String description, String context, String content) {
        Presentation presentation = getPresentation(id);
        presentation.setTitle(title);
        presentation.setDescription(description);
        presentation.setContext(context);
        presentation.setContent(content);
        presentation.setCachedAiContent(null); // Cache zurücksetzen
        
        presentationRepository.save(presentation);
    }

    public void deletePresentation(Long id) {
        presentationRepository.deleteById(id);
    }

    public String generateQrCode(String accessCode) {
        try {
            String baseUrl = ServletUriComponentsBuilder.fromCurrentContextPath().build().toUriString();
            String url = baseUrl + "/p/" + accessCode;
            
            QRCodeWriter qrCodeWriter = new QRCodeWriter();
            BitMatrix bitMatrix = qrCodeWriter.encode(url, BarcodeFormat.QR_CODE, 200, 200);
            
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            MatrixToImageWriter.writeToStream(bitMatrix, "PNG", outputStream);
            
            return Base64.getEncoder().encodeToString(outputStream.toByteArray());
        } catch (WriterException | IOException e) {
            throw new RuntimeException("QR-Code konnte nicht generiert werden", e);
        }
    }

    public String getOrGenerateAiContent(Presentation presentation) {
        if (presentation.getCachedAiContent() != null) {
            return presentation.getCachedAiContent();
        }
        
        List<Feedback> feedbacks = feedbackRepository.findByPresentationId(presentation.getId());
        String aiContent = aiService.generateAiContent(presentation.getContext(), presentation.getContent(), feedbacks);
        
        presentation.setCachedAiContent(aiContent);
        presentation.setLastUpdated(LocalDateTime.now());
        presentationRepository.save(presentation);
        
        return aiContent;
    }

    public void scheduleFeedbackProcessing(Presentation presentation, int processingInterval) {
        presentation.setProcessingScheduled(true);
        presentation.setNextProcessingTime(LocalDateTime.now().plusSeconds(processingInterval));
        presentationRepository.save(presentation);
    }
}
