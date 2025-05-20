package com.presentai.service;

import com.presentai.model.User;
import com.presentai.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new UsernameNotFoundException("Benutzer nicht gefunden: " + username));
    }

    public User registerUser(String username, String password, String registrationPassword, String requiredPassword) {
        if (!registrationPassword.equals(requiredPassword)) {
            throw new IllegalArgumentException("Falsches Registrierungspasswort");
        }

        if (userRepository.findByUsername(username).isPresent()) {
            throw new IllegalArgumentException("Benutzername bereits vergeben");
        }

        User user = new User();
        user.setUsername(username);
        user.setPassword(passwordEncoder.encode(password));

        // Ersten Benutzer zum Admin machen
        if (userRepository.count() == 0) {
            user.setAdmin(true);
        }

        return userRepository.save(user);
    }
}
