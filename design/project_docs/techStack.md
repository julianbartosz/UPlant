    * Purpose: Key technology choices and architecture decisions
    * Update: When significant technology decisions are made or changed
    * Format: Use headers (##) for main technology categories, bullet points for specifics
    * Content: Detail chosen technologies, frameworks, and architectural decisions with brief justifications

# UPlant Tech Stack

This document outlines the primary technologies and architectural decisions driving the UPlant project. It serves as a reference for current development practices and guides future enhancements.

## Frontend

- **React**  
  *Rationale:*  
  Provides a component-based architecture for building a dynamic, interactive user interface. Its robust ecosystem supports efficient state management and UI updates.

- **Vite**  
  *Rationale:*  
  Offers a fast development server with hot module replacement and optimized production builds, streamlining the development workflow.

- **React Router**  
  *Rationale:*  
  Manages client-side routing, ensuring seamless navigation within the single-page application.

- **CSS Modules / Custom CSS**  
  *Rationale:*  
  Supports modular, maintainable styling by encapsulating component-specific styles and preventing global CSS conflicts.

## Backend

- **Django**  
  *Rationale:*  
  A robust framework that supports rapid development, secure authentication, and an ORM for complex data models. Its scalability and built-in features make it ideal for handling the backend logic of UPlant.

- **Django REST Framework (DRF)**  
  *Rationale:*  
  (If applicable) Facilitates the creation of RESTful API endpoints, allowing seamless data communication between the frontend and backend.

- **Allauth & Social Account Providers**  
  *Rationale:*  
  Simplifies user authentication by supporting social logins (e.g., Google, Apple) and managing secure user sessions.

- **Django Extensions & Django Select2**  
  *Rationale:*  
  Enhance developer productivity and enrich user interface components with extended features and select input capabilities.

## Database

- **SQLite (Development)**  
  *Rationale:*  
  Lightweight and easy to set up, making it suitable for local development and testing.

- **PostgreSQL (Production)**  
  *Rationale:*  
  Offers scalability, robust performance, and enhanced security, ensuring a reliable production environment.

## Additional Tools & Libraries

- **ESLint & Prettier**  
  *Rationale:*  
  Enforce code quality and consistent coding styles across the project, aiding in maintainability.

- **Markdown Linting Tools**  
  *Rationale:*  
  Ensure documentation adheres to best practices and remains clean and readable.

- **GitHub Actions**  
  *Rationale:*  
  Automate testing, linting, and documentation review workflows, helping to maintain consistency and quality throughout the development process.

- **Docker**  
  *Rationale:*  
  Provides containerization for consistent development and deployment environments, streamlining the workflow from local to production.

## Architectural Decisions

- **Component-Based UI:**  
  Utilizes React’s modular components to build a reusable and scalable user interface.

- **RESTful API Design:**  
  Structures backend endpoints following REST principles for predictable, scalable data interactions.

- **Separation of Concerns:**  
  Clearly delineates responsibilities between the frontend and backend, allowing for independent development, testing, and future scalability.

- **Scalability and Maintainability:**  
  Designs the system architecture to accommodate growth, new features, and performance optimizations over time.

## Future Considerations

- **Microservices Architecture:**  
  Evaluate transitioning to a microservices approach to further enhance scalability and isolation of system components.

- **GraphQL Integration:**  
  Explore GraphQL as an alternative to REST for more flexible, efficient data queries as the project evolves.

- **Enhanced Security Protocols:**  
  Continuously assess and improve authentication mechanisms and data protection measures in line with industry best practices.
