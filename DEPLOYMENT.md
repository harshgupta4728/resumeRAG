# ResumeRAG Deployment Guide

## Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd resume-rag-hackathon
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Test Credentials

- **Recruiter**: `recruiter@example.com` / `strongpassword`
- **Candidate**: `candidate@example.com` / `strongpassword`

## Production Deployment

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://host:port
```

### Database Setup

1. **Install PostgreSQL with pgvector:**
   ```bash
   # Using Docker
   docker run --name postgres-pgvector -e POSTGRES_PASSWORD=password -p 5432:5432 -d pgvector/pgvector:pg15
   ```

2. **Create database:**
   ```sql
   CREATE DATABASE resumerag;
   ```

### Redis Setup

```bash
# Using Docker
docker run --name redis -p 6379:6379 -d redis:7-alpine
```

### Backend Deployment

1. **Build and run:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python init_db.py  # Initialize database
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Deployment

1. **Build for production:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Serve with nginx:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           root /path/to/frontend/dist;
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Health Checks

- Backend: `GET http://localhost:8000/health`
- Frontend: Check if the React app loads
- Database: `docker exec -it postgres-pgvector pg_isready -U postgres`
- Redis: `docker exec -it redis redis-cli ping`

## Monitoring

- Check logs: `docker-compose logs -f`
- Monitor resources: `docker stats`
- Database monitoring: Use pgAdmin or similar tools

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Database connection**: Check DATABASE_URL format
3. **Redis connection**: Verify Redis is running
4. **File uploads**: Check file size limits and permissions

### Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis
```

## Security Considerations

1. **Change default secrets** in production
2. **Use HTTPS** for production deployments
3. **Configure firewall** rules
4. **Regular security updates** for dependencies
5. **Database backups** and disaster recovery
6. **Monitor rate limiting** and abuse

## Scaling

### Horizontal Scaling

1. **Load balancer** for multiple backend instances
2. **Database read replicas** for read-heavy workloads
3. **Redis cluster** for high availability
4. **CDN** for static frontend assets

### Performance Optimization

1. **Database indexing** on frequently queried columns
2. **Caching strategies** for expensive operations
3. **Connection pooling** for database connections
4. **Compression** for API responses

## Backup and Recovery

### Database Backup

```bash
# Create backup
pg_dump -h localhost -U postgres resumerag > backup.sql

# Restore backup
psql -h localhost -U postgres resumerag < backup.sql
```

### Application Backup

1. **Code repository** (Git)
2. **Environment configuration**
3. **Database dumps**
4. **File uploads** (if stored locally)

## Maintenance

### Regular Tasks

1. **Update dependencies** regularly
2. **Monitor disk space** and database growth
3. **Review logs** for errors and performance issues
4. **Backup data** on schedule
5. **Security patches** and updates

### Monitoring

- **Application metrics**: Response times, error rates
- **Database metrics**: Query performance, connection counts
- **System metrics**: CPU, memory, disk usage
- **Business metrics**: User activity, file uploads

---

For additional support, check the main README.md or create an issue in the repository.
