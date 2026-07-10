module.exports = {
  apps: [
    {
      name: 'railyatra-backend',
      script: './apps/backend/dist/main.js',
      instances: process.env.NODE_ENV === 'production' ? 'max' : 1,
      exec_mode: process.env.NODE_ENV === 'production' ? 'cluster' : 'fork',
      env: {
        NODE_ENV: process.env.NODE_ENV || 'production',
        PORT: process.env.PORT || 5000,
        DATABASE_URL: process.env.DATABASE_URL || 'file:./prisma/dev.db',
        JWT_SECRET: process.env.JWT_SECRET || 'super-secure-production-jwt-key-123',
        REDIS_HOST: process.env.REDIS_HOST || 'localhost',
        REDIS_PORT: process.env.REDIS_PORT || 6379,
        AI_SERVICE_URL: process.env.AI_SERVICE_URL || 'http://localhost:8000',
        CORS_ORIGIN: process.env.CORS_ORIGIN || '*'
      },
      listen_timeout: 15000,
      kill_timeout: 20000,
      max_restarts: 3,
      min_uptime: 5000
    },
    {
      name: 'railyatra-ai-service',
      script: './apps/ai-service/venv/Scripts/python.exe',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      env: {
        ENV: process.env.NODE_ENV || 'production',
        PORT: 8000,
        REDIS_URL: process.env.REDIS_URL || 'redis://localhost:6379/0',
        QDRANT_URL: process.env.QDRANT_URL || 'http://localhost:6333',
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
        GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
        CORS_ORIGIN: process.env.CORS_ORIGIN || '*'
      },
      max_restarts: 3,
      min_uptime: 5000
    }
  ]
};
