# UPlant Frontend

This document provides comprehensive information about the frontend implementation of the UPlant application.

## Technology Stack

- **Framework**: React 18.3.1
- **Build Tool**: Vite 6.0.5
- **Package Manager**: NPM
- **Language**: JavaScript/JSX

## Getting Started

### Prerequisites

- Node.js (v16.x or higher recommended)
- npm (v8.x or higher recommended)

### Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```
   cd UPlant/frontend
   ```
3. Install dependencies:
   ```
   npm install
   ```

### Development

Start the development server:

```
npm run dev
```

The application will be available at [http://localhost:5173](http://localhost:5173) by default.

## UI Framework Details

The frontend is built with React and uses the following major libraries:

- **React Router Dom (v7.4.1)**: For client-side routing and navigation
- **React DnD (v16.0.1)**: For drag-and-drop functionality
- **Framer Motion (v12.9.2)**: For animations and transitions
- **React Icons (v5.4.0)**: For icon components
- **React Select (v5.10.1)**: For enhanced select inputs
- **React Switch (v7.1.0)**: For toggle switches
- **React Tooltip (v5.28.0)**: For tooltips
- **React Loader Spinner (v6.1.6)**: For loading indicators
- **Axios (v1.8.4)**: For HTTP requests to the backend API

## Component Structure

The application follows a modular component structure:

```
src/
├── assets/            # Static assets like images and global styles
├── components/        # Reusable UI components
│   ├── common/        # Shared components (buttons, inputs, etc.)
│   ├── layout/        # Layout components (header, footer, etc.)
│   └── specific/      # Feature-specific components
├── context/           # React context providers
├── hooks/             # Custom React hooks
├── pages/             # Page components that correspond to routes
├── styles/            # Global and component-specific styles
├── constants/         # Application constants and configuration
├── App.jsx            # Main application component
└── index.jsx          # Application entry point
```

### Component Guidelines

- Components should be focused on a single responsibility
- Use functional components with hooks rather than class components
- Keep components small and maintainable
- Use proper prop validation

## Styling Guidelines

The project uses CSS modules for component-specific styling:

- Each component should have its own CSS module file
- Use semantic class names
- Follow BEM naming convention when appropriate
- Use CSS variables for theme colors, spacing, and typography
- Responsive design should be implemented using media queries
- Component-specific styles should be kept close to the component they style

## State Management

State management is handled primarily through:

- React's built-in useState and useReducer hooks for local state
- React Context API for global state
- Custom hooks for shared stateful logic

## Build Process

The build process is managed by Vite:

1. **Development**: `npm run dev` - Starts the development server with hot module replacement
2. **Linting**: `npm run lint` - Runs ESLint on all JavaScript files
3. **Build**: `npm run build` - Creates an optimized production build in the `dist` directory
4. **Preview**: `npm run preview` - Serves the production build locally for testing

### Build Configuration

Vite is configured in `vite.config.js` with the following features:
- React SWC plugin for fast refresh
- Optimized asset handling
- Environment variable processing

## API Integration

Communication with the backend is handled through Axios:
- API endpoints are organized by feature
- Requests use proper error handling
- Authentication tokens are managed automatically

## Testing Strategy

The project is set up for testing with:
- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for critical user flows

## Browser Support

The application is designed to work on:

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

Mobile browsers:
- iOS Safari (latest 2 versions)
- Android Chrome (latest 2 versions)

## Performance Considerations

- Code splitting using dynamic imports
- Lazy loading of components not needed for initial render
- Image optimization
- Minimizing bundle size through dependency management

## Security Considerations

- User input validation
- Secure storage of sensitive information
- CSRF protection
- XSS prevention

## Contributing

1. Follow the coding style and guidelines
2. Write clear, descriptive commit messages
3. Document new features and changes
4. Add tests for new functionality
5. Ensure all tests pass before submitting pull requests

## License

[Include license information here]
