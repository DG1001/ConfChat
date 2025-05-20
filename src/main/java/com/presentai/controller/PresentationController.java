package com.presentai.controller;

import com.presentai.model.Feedback;
import com.presentai.model.Presentation;
import com.presentai.model.User;
import com.presentai.service.FeedbackService;
import com.presentai.service.PresentationService;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Controller
public class PresentationController {

    @Autowired
    private PresentationService presentationService;

    @Autowired
    private FeedbackService feedbackService;

    @Autowired
    private Parser markdownParser;

    @Autowired
    private HtmlRenderer htmlRenderer;

    @Value("${feedback.processing.interval:30}")
    private int feedbackProcessingInterval;

    @Value("${client.refresh.interval:20}")
    private int clientRefreshInterval;

    @GetMapping("/dashboard")
    public String dashboard(@AuthenticationPrincipal User user, Model model) {
        List<Presentation> presentations = presentationService.getPresentationsByUser(user);
        model.addAttribute("presentations", presentations);
        return "dashboard";
    }

    @GetMapping("/presentation/new")
    public String newPresentationForm() {
        return "new_presentation";
    }

    @PostMapping("/presentation/new")
    public String createPresentation(
            @RequestParam String title,
            @RequestParam String description,
            @RequestParam String context,
            @RequestParam String content,
            @AuthenticationPrincipal User user) {
        
        presentationService.createPresentation(title, description, context, content, user);
        return "redirect:/dashboard";
    }

    @GetMapping("/presentation/{id}")
    public String viewPresentation(@PathVariable Long id, @AuthenticationPrincipal User user, Model model) {
        Presentation presentation = presentationService.getPresentation(id);
        
        // Überprüfen, ob der Benutzer der Ersteller ist
        if (!presentation.getCreator().getId().equals(user.getId()) && !user.isAdmin()) {
            return "redirect:/dashboard";
        }
        
        // QR-Code generieren
        String qrCode = presentationService.generateQrCode(presentation.getAccessCode());
        String presentationUrl = "/p/" + presentation.getAccessCode();
        
        List<Feedback> feedbacks = feedbackService.getFeedbacksByPresentation(id);
        
        model.addAttribute("presentation", presentation);
        model.addAttribute("qrCode", qrCode);
        model.addAttribute("presentationUrl", presentationUrl);
        model.addAttribute("feedbacks", feedbacks);
        
        return "view_presentation";
    }

    @GetMapping("/presentation/{id}/edit")
    public String editPresentationForm(@PathVariable Long id, @AuthenticationPrincipal User user, Model model) {
        Presentation presentation = presentationService.getPresentation(id);
        
        // Überprüfen, ob der Benutzer der Ersteller ist
        if (!presentation.getCreator().getId().equals(user.getId()) && !user.isAdmin()) {
            return "redirect:/dashboard";
        }
        
        model.addAttribute("presentation", presentation);
        return "edit_presentation";
    }

    @PostMapping("/presentation/{id}/edit")
    public String updatePresentation(
            @PathVariable Long id,
            @RequestParam String title,
            @RequestParam String description,
            @RequestParam String context,
            @RequestParam String content,
            @AuthenticationPrincipal User user) {
        
        Presentation presentation = presentationService.getPresentation(id);
        
        // Überprüfen, ob der Benutzer der Ersteller ist
        if (!presentation.getCreator().getId().equals(user.getId()) && !user.isAdmin()) {
            return "redirect:/dashboard";
        }
        
        presentationService.updatePresentation(id, title, description, context, content);
        return "redirect:/presentation/" + id;
    }

    @PostMapping("/presentation/{id}/delete")
    public String deletePresentation(@PathVariable Long id, @AuthenticationPrincipal User user) {
        Presentation presentation = presentationService.getPresentation(id);
        
        // Überprüfen, ob der Benutzer der Ersteller ist
        if (!presentation.getCreator().getId().equals(user.getId()) && !user.isAdmin()) {
            return "redirect:/dashboard";
        }
        
        presentationService.deletePresentation(id);
        return "redirect:/dashboard";
    }

    @GetMapping("/p/{accessCode}")
    public String publicView(@PathVariable String accessCode, Model model) {
        try {
            Presentation presentation = presentationService.getPresentationByAccessCode(accessCode);
            
            // KI-Inhalte abrufen oder generieren
            String aiContent = presentationService.getOrGenerateAiContent(presentation);
            
            // Markdown zu HTML konvertieren
            String aiContentHtml = htmlRenderer.render(markdownParser.parse(aiContent));
            
            // Status der Verarbeitung
            Map<String, Object> processingStatus = new HashMap<>();
            processingStatus.put("scheduled", presentation.isProcessingScheduled());
            processingStatus.put("nextUpdate", presentation.getNextProcessingTime());
            
            model.addAttribute("presentation", presentation);
            model.addAttribute("aiContent", aiContent);
            model.addAttribute("aiContentHtml", aiContentHtml);
            model.addAttribute("processingStatus", processingStatus);
            model.addAttribute("clientRefreshInterval", clientRefreshInterval);
            
            return "public_view";
        } catch (IllegalArgumentException e) {
            return "redirect:/";
        }
    }

    @PostMapping("/p/{accessCode}/feedback")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> submitFeedback(
            @PathVariable String accessCode,
            @RequestParam String feedback) {
        
        try {
            Presentation presentation = presentationService.getPresentationByAccessCode(accessCode);
            
            // Feedback speichern
            feedbackService.createFeedback(feedback, presentation);
            
            // Verarbeitung planen
            presentationService.scheduleFeedbackProcessing(presentation, feedbackProcessingInterval);
            
            // Temporäre Antwort zurückgeben
            String tempResponse = "Ihre Anfrage wurde entgegengenommen und wird verarbeitet. Die Seite wird in Kürze aktualisiert.";
            String tempResponseHtml = "<p>" + tempResponse + "</p><p><em>Wird verarbeitet...</em></p>";
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("aiResponse", tempResponse);
            response.put("aiResponseHtml", tempResponseHtml);
            response.put("processing", true);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.badRequest().body(response);
        }
    }

    @GetMapping("/api/feedbacks/{presentationId}")
    @ResponseBody
    public ResponseEntity<List<Feedback>> getFeedbacks(@PathVariable Long presentationId) {
        List<Feedback> feedbacks = feedbackService.getFeedbacksByPresentation(presentationId);
        return ResponseEntity.ok(feedbacks);
    }

    @PostMapping("/api/generate_preview")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> generatePreview(@RequestBody Map<String, String> data) {
        String context = data.get("context");
        String content = data.get("content");
        
        if (context == null || content == null || context.isEmpty() || content.isEmpty()) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", "Kontext und Inhalt sind erforderlich");
            return ResponseEntity.badRequest().body(response);
        }
        
        try {
            Presentation tempPresentation = new Presentation();
            tempPresentation.setContext(context);
            tempPresentation.setContent(content);
            
            String aiContent = presentationService.getOrGenerateAiContent(tempPresentation);
            
            String previewHtml = htmlRenderer.render(markdownParser.parse(aiContent));
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("preview", aiContent);
            response.put("previewHtml", previewHtml);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.badRequest().body(response);
        }
    }
}
