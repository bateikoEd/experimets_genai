# AI Question-Answering System Architecture

## Overview

This document outlines the architecture for an AI-powered question-answering system that leverages the existing house price dataset, integrates with PostgreSQL using MCP (Model Context Protocol), and connects to LM Studio for LLM capabilities, with a Streamlit-based user interface.

## System Architecture

```mermaid
graph TB
    subgraph "Data Layer"
        CSV[House Prices CSV]
        PG[(PostgreSQL Database)]
        VectorDB[(Vector Database)]
    end
    
    subgraph "Processing Layer"
        MCP[MCP Protocol Server]
        DataProcessor[Data Processing Pipeline]
        Embedder[Embedding Generator]
    end
    
    subgraph "AI Layer"
        LMStudio[LM Studio Server]
        LLM[LLM Model]
        RAG[RAG System]
    end
    
    subgraph "API Layer"
        API[REST API Server]
        QA[Question-Answering Endpoint]
        DataAPI[Data Management Endpoint]
    end
    
    subgraph "Client Layer"
        Streamlit[Streamlit UI]
        CLI[CLI Tool]
    end
    
    CSV --> DataProcessor
    DataProcessor --> PG
    DataProcessor --> VectorDB
    PG --> MCP
    VectorDB --> RAG
    RAG --> LLM
    LLM --> LMStudio
    API --> QA
    API --> DataAPI
    QA --> RAG
    DataAPI --> PG
    Streamlit --> API
    CLI --> API
```

## Component Details

### 1. Data Layer

#### PostgreSQL Database
- **Purpose**: Store structured house price data and metadata
- **Schema Design**:
  - `houses` table: Contains all house price records
  - `questions` table: Stores user questions and answers
  - `sessions` table: Tracks user sessions
  - `embeddings` table: Stores vector embeddings for semantic search

#### Vector Database
- **Purpose**: Store embeddings for semantic search and RAG
- **Technology**: ChromaDB
- **Content**: House descriptions, features, and metadata embeddings

### 2. Processing Layer

#### MCP Protocol Server
- **Purpose**: Bridge between PostgreSQL and AI components
- **Responsibilities**:
  - Handle database operations via MCP
  - Provide structured data access to LLM
  - Execute complex queries and aggregations

#### Data Processing Pipeline
- **CSV Import**: Parse and validate house price data
- **Data Cleaning**: Handle missing values, outliers, and normalization
- **Feature Engineering**: Create relevant features for ML and AI
- **Data Validation**: Ensure data quality and consistency

#### Embedding Generator
- **Purpose**: Convert text data to vector embeddings
- **Model**: OpenAI embeddings or similar
- **Output**: Vector representations for semantic search

### 3. AI Layer

#### LM Studio Integration
- **Purpose**: Provide LLM capabilities for question answering
- **Connection**: HTTP API to LM Studio server
- **Models**: GPT-oss 20b
- **Configuration**: Configurable model parameters and endpoints

#### RAG (Retrieval-Augmented Generation) System
- **Purpose**: Enhance LLM responses with relevant data
- **Components**:
  - Document retriever (vector search)
  - Context builder
  - Response generator
- **Benefits**: Factual accuracy, reduced hallucinations

### 4. API Layer

#### REST API Server
- **Technology**: FastAPI 
- **Port**: 8000
- **Base URL**: `/api/v1`

#### Endpoints

##### Question-Answering Endpoint
- **Path**: `/api/v1/ask`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "question": "What is the average house price in Austin?",
    "context": {},
    "session_id": "optional_session_id"
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The average house price in Austin is $350,000...",
    "sources": ["house_123", "house_456"],
    "confidence": 0.95
  }
  ```

##### Data Management Endpoint
- **Path**: `/api/v1/data`
- **Methods**: GET, POST, PUT, DELETE
- **Features**: CRUD operations for house data

##### Health Check Endpoint
- **Path**: `/api/v1/health`
- **Method**: GET
- **Response**: System status and component health

### 5. Client Layer

#### Web Interface
- **Technology**: React/Vue.js
- **Features**: Interactive dashboard, question input, response visualization

#### CLI Tool
- **Purpose**: Command-line interface for testing and automation
- **Commands**: `ask`, `query`, `export`

#### Mobile App
- **Technology**: React Native or Flutter
- **Features**: On-the-go question answering

## Data Flow

### 1. Data Ingestion Flow
```mermaid
sequenceDiagram
    participant CSV as CSV File
    participant DP as Data Processor
    participant PG as PostgreSQL
    participant VDB as Vector Database
    
    CSV->>DP: Load and parse CSV
    DP->>DP: Clean and validate data
    DP->>PG: Store structured data
    DP->>VDB: Generate and store embeddings
```

### 2. Question Answering Flow
```mermaid
sequenceDiagram
    participant User as User
    participant API as API Server
    participant RAG as RAG System
    participant LM as LM Studio
    participant PG as PostgreSQL
    participant VDB as Vector Database
    
    User->>API: Submit question
    API->>RAG: Process question
    RAG->>VDB: Semantic search
    RAG->>PG: Structured query
    VDB-->>RAG: Relevant documents
    PG-->>RAG: Structured data
    RAG->>LM: Generate answer
    LM-->>RAG: LLM response
    RAG-->>API: Enhanced answer
    API-->>User: Final response
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + Vector Database
- **AI**: LM Studio + OpenAI/Anthropic models
- **Protocol**: MCP for database access
- **Authentication**: JWT tokens

### Frontend
- **Framework**: React.js
- **State Management**: Redux/Context API
- **UI Components**: Material-UI/Ant Design

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)
1. Set up PostgreSQL database with house price data
2. Implement MCP protocol server
3. Create basic data processing pipeline
4. Set up LM Studio integration

### Phase 2: Core Features (Weeks 3-4)
1. Develop RAG system
2. Implement question-answering endpoint
3. Create vector database integration
4. Build basic API server

### Phase 3: Enhancement (Weeks 5-6)
1. Add web interface
2. Implement CLI tool
3. Add authentication and authorization
4. Create comprehensive testing suite

### Phase 4: Production (Weeks 7-8)
1. Set up monitoring and logging
2. Performance optimization
3. Documentation and deployment
4. User testing and feedback

## Configuration

### Environment Variables
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/house_prices
VECTOR_DB_URL=http://localhost:8080

# LM Studio Configuration
LM_STUDIO_URL=http://localhost:1234
LM_STUDIO_MODEL=gpt-4
LM_STUDIO_API_KEY=your_api_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your_secret_key

# MCP Configuration
MCP_SERVER_URL=http://localhost:8001
MCP_API_KEY=your_mcp_key

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Docker Configuration
```dockerfile
# Backend Service
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Streamlit Configuration
```dockerfile
# Streamlit UI Service
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY streamlit_app.py .
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LM_STUDIO_URL=${LM_STUDIO_URL}
    depends_on:
      - postgres
      - vector-db
  
  streamlit:
    build: ./streamlit
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=house_prices
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  vector-db:
    image: weaviate/weaviate:latest
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  postgres_data:
  weaviate_data:
```

## Security Considerations

1. **Data Privacy**: Anonymize sensitive information
2. **API Security**: Rate limiting, authentication, authorization
3. **Database Security**: Encryption at rest and in transit
4. **Model Security**: Input validation, output filtering

## Performance Optimization

1. **Caching**: Redis for frequent queries
2. **Indexing**: Database and vector database optimization
3. **Load Balancing**: Multiple API instances
4. **Asynchronous Processing**: Background tasks for heavy operations

## Monitoring and Logging

1. **Health Checks**: Regular system health monitoring
2. **Performance Metrics**: Response times, error rates
3. **Logging**: Structured logging with correlation IDs
4. **Alerting**: Real-time notifications for issues

## Scalability

1. **Horizontal Scaling**: Load balancing across multiple instances
2. **Database Scaling**: Read replicas, connection pooling
3. **Vector Database Scaling**: Sharding and replication
4. **Auto-scaling**: Kubernetes-based auto-scaling

## Testing Strategy

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: API and database integration
3. **End-to-End Tests**: Complete user workflows
4. **Performance Tests**: Load and stress testing
``