# Spec: login-ui

## Overview
Rediseño de la pantalla de login con diseño moderno y formulario de registro público integrado.

## ADDED Requirements

### Requirement: Login form
The system SHALL display a login form with email and password fields, a submit button, and a link to switch to registration.

#### Scenario: Successful login
- **WHEN** the user enters valid credentials and clicks "Iniciar sesión"
- **THEN** the system authenticates the user
- **AND** redirects to the dashboard

#### Scenario: Failed login
- **WHEN** the user enters invalid credentials
- **THEN** the system displays an error message inside the login card
- **AND** does not redirect

#### Scenario: Empty fields
- **WHEN** the user clicks "Iniciar sesión" with empty fields
- **THEN** the system shows validation errors on the empty fields
- **AND** does not submit the form

### Requirement: Registration form
The system SHALL display a registration form when the user toggles to "Registrarse", with email, password, and confirm password fields.

#### Scenario: Successful registration
- **WHEN** the user enters valid data and clicks "Crear cuenta"
- **THEN** the system creates the user with role ALUMNO
- **AND** displays a success message
- **AND** switches to the login form after 2 seconds

#### Scenario: Password mismatch
- **WHEN** the user enters different passwords in "Contraseña" and "Confirmar contraseña"
- **THEN** the system shows a validation error
- **AND** does not submit

#### Scenario: Duplicate email
- **WHEN** the user registers with an email that already exists
- **THEN** the system shows an error message "El email ya está registrado"
- **AND** stays on the registration form

### Requirement: Toggle between login and register
The system SHALL allow the user to switch between login and registration forms without navigating to a different page.

#### Scenario: Switch to register
- **WHEN** the user clicks "¿No tenés cuenta? Registrate"
- **THEN** the form transitions to the registration view with a smooth animation

#### Scenario: Switch to login
- **WHEN** the user clicks "Ya tenés cuenta? Iniciá sesión"
- **THEN** the form transitions to the login view with a smooth animation

### Requirement: Visual design
The login page SHALL have a modern, centered design with branding elements.

#### Scenario: Desktop layout
- **WHEN** viewed on a desktop screen (≥768px)
- **THEN** the form card is centered vertically and horizontally
- **AND** shows a logo/brand above the card

#### Scenario: Mobile layout
- **WHEN** viewed on a mobile screen (<768px)
- **THEN** the form card takes full width with some padding
- **AND** is responsive and usable
