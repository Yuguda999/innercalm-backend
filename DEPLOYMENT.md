# InnerCalm Backend Deployment Guide

## Environment Variables for Vercel Deployment

Set these environment variables in your Vercel project dashboard:

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_actual_openai_api_key_here

# Database Configuration
DATABASE_URL=your_actual_postgresql_database_url_here

# Security Configuration
SECRET_KEY=your-secure-random-secret-key-for-jwt-signing

# Environment
DEBUG=False

# CORS Configuration (Update with your actual frontend URL)
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,https://innercalm-frontend.vercel.app

# AI Configuration (Optional - uses defaults if not set)
MAX_CONVERSATION_HISTORY=20
EMOTION_ANALYSIS_THRESHOLD=0.5
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
OPENAI_MODEL=gpt-4
```

## Deployment Steps

1. **Push to GitHub** (after removing sensitive data)
2. **Create Vercel Project**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
3. **Configure Environment Variables**
   - Go to Project Settings > Environment Variables
   - Add all the variables listed above with your actual values
4. **Deploy**
   - Vercel will automatically deploy your application

## Database Setup

The PostgreSQL database is already configured and ready:
- ✅ Database connection tested
- ✅ All tables created
- ✅ Production ready

## Local Development

1. Copy `.env.local` to `.env` (if you have the local file):
   ```bash
   cp .env.local .env
   ```

2. Or create `.env` with your local configuration:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=your_database_url
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Security Notes

- Never commit actual API keys or database credentials to Git
- Use Vercel environment variables for all sensitive data
- Rotate API keys regularly
- Use strong, unique SECRET_KEY for JWT signing

## Troubleshooting

If deployment fails:
1. Check Vercel build logs
2. Verify all environment variables are set
3. Ensure database is accessible from Vercel
4. Check CORS configuration matches frontend domain
