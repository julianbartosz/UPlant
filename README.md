# UPlant 🌱

UPlant is a comprehensive plant management application designed to help users track, care for, and manage their plant collections. The application provides tools for monitoring watering schedules, tracking plant growth, organizing plants into gardens, and connecting with a community of plant enthusiasts.

## Features

- **Plant Management**: Track detailed information about your plants, including species, care requirements, and health status
- **Garden Organization**: Create and manage virtual gardens to organize your plant collection
- **Watering Reminders**: Receive notifications when plants need watering based on species-specific care requirements
- **Community Interaction**: Share photos, tips, and questions with other plant enthusiasts
- **Plant Identification**: Search comprehensive plant database with detailed species information
- **Responsive Design**: Optimized for both desktop and mobile use

## Technology Stack

### Backend
- **Framework**: Django 4.2 with Django REST Framework
- **Database**: MySQL
- **Authentication**: Django AllAuth, Token Authentication
- **Testing**: Pytest, Factory Boy
- **Deployment**: Docker

### Frontend
- **Framework**: React 18 with Vite
- **State Management**: React Context API
- **Styling**: CSS Modules, Custom Styling
- **HTTP Client**: Axios
- **Testing**: React Testing Library

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js (v16+)
- MySQL Server
- Docker (optional)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd UPlant
```

2. Set up the backend
```bash
cd backend/root
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

3. Set up the frontend
```bash
cd ../../frontend
npm install
npm run dev
```

4. Alternatively, use Docker Compose
```bash
docker-compose up -d
```

## Usage Examples

### Managing Your Plants
1. Add plants to your collection with details like species, acquisition date, and location
2. Track watering, fertilizing, and other care activities
3. Receive notifications when care is needed

### Creating a Garden
1. Create a new garden space with custom dimensions
2. Add plants to your garden with drag-and-drop functionality
3. Visualize plant placement and optimize space usage

### Community Features
1. Share photos of your plants and gardens
2. Ask questions and provide answers to the community
3. Discover new plants and care techniques

## Documentation

- [Backend Documentation](/backend/root/README.md)
- [Frontend Documentation](/frontend/README.md)
- [API Documentation](http://localhost:8000/api/docs/) (when running locally)
- [Database Schema](/backend/root/README.md#database-schema)

## Contributing

We welcome contributions to the UPlant project! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the coding style and guidelines of each project section
- Write clear, descriptive commit messages
- Add tests for new functionality
- Document new features and changes
- Ensure all tests pass before submitting pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- The UPlant team: Jason, Cainan, Beckett, Laura, Julian, and Alex
- All plant data is sourced from public botanical databases
- Icons from Font Awesome


