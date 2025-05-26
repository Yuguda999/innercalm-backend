# InnerCalm Backend

AI-powered emotional healing companion backend built with FastAPI, PostgreSQL, and OpenAI GPT-4.

## Features

- **Empathetic AI Chat**: Conversational AI with therapeutic responses
- **Emotion Analysis**: Advanced sentiment analysis using HuggingFace models
- **Personalized Recommendations**: Custom healing exercises based on emotional patterns
- **Progress Tracking**: Comprehensive emotional journey analytics
- **User Authentication**: Secure JWT-based authentication
- **PostgreSQL Database**: Production-ready database with comprehensive schema

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Production database
- **SQLAlchemy**: Database ORM
- **OpenAI GPT-4**: AI chat capabilities
- **HuggingFace Transformers**: Emotion analysis
- **JWT**: Authentication
- **Pydantic**: Data validation

## Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd innercalm-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## Production Deployment on Vercel

### Prerequisites
- Vercel account
- PostgreSQL database (configured)
- OpenAI API key

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Configure environment variables in Vercel dashboard:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `SECRET_KEY`: A secure random string for JWT signing
     - `ALLOWED_ORIGINS`: Your frontend URL (comma-separated)
     - `DEBUG`: `False`

3. **Environment Variables**
   Set these in your Vercel project settings:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=postgresql://user:password@host:port/database
   SECRET_KEY=your_secure_secret_key
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
   DEBUG=False
   ```

## API Documentation

Once deployed, API documentation is available at:
- **Swagger UI**: `https://your-api-domain.vercel.app/docs` (development only)
- **ReDoc**: `https://your-api-domain.vercel.app/redoc` (development only)

## Database Schema

The application uses the following main tables:
- `users`: User accounts and profiles
- `conversations`: Chat conversations
- `messages`: Individual chat messages
- `emotion_analyses`: Emotion analysis results
- `recommendations`: Personalized recommendations
- `analytics_events`: User interaction analytics

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

### Chat
- `POST /chat/message` - Send chat message
- `GET /chat/conversations` - Get user conversations
- `GET /chat/conversations/{id}` - Get specific conversation

### Emotions
- `GET /emotions/analysis` - Get emotion analysis
- `GET /emotions/patterns` - Get emotion patterns

### Recommendations
- `GET /recommendations` - Get personalized recommendations
- `POST /recommendations/{id}/feedback` - Provide feedback

### Analytics
- `GET /analytics/dashboard` - Get user analytics dashboard

## Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration for frontend integration
- Environment-based configuration
- SQL injection protection via SQLAlchemy ORM

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
