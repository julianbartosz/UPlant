    * Purpose: Concise overview of project structure and recent changes
    * Update: When significant changes affect the overall structure
    * Include sections on:
        * Key Components and Their Interactions
        * Data Flow
        * External Dependencies (including detailed management of libraries, APIs, etc.)
        * Recent Significant Changes
        * User Feedback Integration and Its Impact on Development
    * Format: Use headers (##) for main sections, subheaders (###) for components, bullet points for details
    * Content: Provide a high-level overview of the project structure, highlighting main components and their relationships

# Codebase Summary

## Overview
UPlant is a virtual community garden platform that combines a modern React-based frontend with a robust Django backend. This document provides a high-level overview of the project structure, key interactions between components, data flow, and external dependencies, along with a summary of recent changes and user feedback integration.

## Key Components and Their Interactions

### Frontend
- **React Application:**  
  - Located in `/frontend`.
  - **Main Components:**  
    - **Garden Dashboard:** Includes the dynamic garden grid in `frontend/src/components/GardenSection/Garden.jsx`.
  - **Routing:**  
    - Managed by React Router, with key routes such as `/garden`.

### Backend
- **Django Application:**  
  - Located in `/backend/root`.
  - **Core Modules:**  
    - **Authentication & User Management:** Uses Django Allauth and a custom user model.
    - **Garden & Plant Management:** Handled within the core app (`/backend/root/core`) with models enforcing data integrity.
  - **API & Integration:**  
    - RESTful endpoints (or future API endpoints) facilitate data exchange with the frontend.

### Documentation and Design Assets
- **Design Documents:**  
  - Located in `/design/docs` (includes FRS, URS, wireframes, and technology surveys).
- **Static Assets:**  
  - Managed in `/backend/root/static` and `/design/assets`, supporting both UI design and project branding.

## Data Flow

- **User Authentication Flow:**  
  - Users sign in via the React Login page, which communicates securely with Django endpoints.
- **Garden Data Flow:**  
  - Garden information and plant data are retrieved from Django models and rendered dynamically in the React components.
- **API Communication:**  
  - Any data exchanged between the frontend and backend adheres to RESTful standards, ensuring a predictable and scalable flow.

## External Dependencies

- **Frontend Libraries & Tools:**  
  - React, Vite, and React Router for building and navigating the user interface.
- **Backend Frameworks & Extensions:**  
  - Django, Django Allauth, Django Extensions, and (optionally) Django REST Framework for API development.
- **Third-Party Services:**  
  - Social authentication providers (Google, Apple) for seamless user logins.
- **Package Management:**  
  - npm for frontend packages and pip for backend dependencies.

## Recent Significant Changes

- **Login Workflow Refactor:**  
  - Transitioned from a Django template-based login to a React-based login component.
- **UI Enhancements:**  
  - Updated the garden dashboard to incorporate dynamic grid rendering and responsive design improvements.
- **Backend Model Adjustments:**  
  - Revised data constraints in models (e.g., Gardens, Garden_log) to improve data integrity and scalability.

## User Feedback Integration

- **Feedback Channels:**  
  - Collected via beta testing sessions and user surveys.
- **Impact on Development:**  
  - Initiated UI refinements to enhance usability and responsiveness.
  - Adjusted backend endpoints and data flows to address performance concerns reported by users.
- **Planned Iterations:**  
  - Future enhancements include advanced notification features and an enriched discussion board, based on ongoing user feedback.

## Summary and Next Steps

- **Project Health:**  
  - The project is actively evolving with structured updates and continuous user feedback integration.
- **Next Steps:**  
  1. Finalize and deploy the updated React-based login workflow.
  2. Enhance garden visualization and community interaction features.
  3. Expand and refine API documentation to support upcoming features.
  4. Monitor user feedback and iterate on UI/UX improvements for better engagement.
