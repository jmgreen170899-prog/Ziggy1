# ZiggyAI System Architecture

This document provides detailed architecture diagrams for the ZiggyAI trading platform using Mermaid notation.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Data Flow](#data-flow)
- [Trading System](#trading-system)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Database Schema](#database-schema)
- [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile App]
    end

    subgraph "Frontend - Next.js"
        UI[React UI Components]
        STATE[Zustand State]
        API_CLIENT[API Client]
        WS_CLIENT[WebSocket Client]
    end

    subgraph "Backend - FastAPI"
        API[REST API Routes]
        WS[WebSocket Server]
        AUTH[Auth Service]
        
        subgraph "Core Services"
            TRADING[Trading Engine]
            PAPER[Paper Broker]
            ML[ML Learner]
            RAG[RAG Pipeline]
        end
        
        subgraph "Background Workers"
            SCHEDULER[APScheduler]
            PAPER_WORKER[Paper Worker]
            NEWS_STREAM[News Streaming]
        end
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        QDRANT[(Qdrant Vector DB)]
        REDIS[(Redis Cache)]
    end

    subgraph "External Services"
        POLYGON[Polygon.io]
        ALPACA[Alpaca API]
        YFINANCE[Yahoo Finance]
        OPENAI[OpenAI API]
        NEWS[NewsAPI]
    end

    WEB --> UI
    MOBILE --> UI
    UI --> STATE
    UI --> API_CLIENT
    UI --> WS_CLIENT
    
    API_CLIENT --> API
    WS_CLIENT --> WS
    
    API --> AUTH
    API --> TRADING
    API --> RAG
    
    TRADING --> PAPER
    TRADING --> ML
    
    SCHEDULER --> PAPER_WORKER
    SCHEDULER --> NEWS_STREAM
    
    PAPER --> POSTGRES
    ML --> POSTGRES
    RAG --> QDRANT
    AUTH --> REDIS
    
    TRADING --> POLYGON
    TRADING --> ALPACA
    TRADING --> YFINANCE
    RAG --> OPENAI
    NEWS_STREAM --> NEWS
```

---

## Backend Architecture

### API Router Structure

```mermaid
graph LR
    subgraph "FastAPI Application"
        MAIN[main.py]
        
        subgraph "API Routers"
            CORE[routes.py<br/>Core/RAG]
            AUTH_R[routes_auth.py<br/>Authentication]
            MARKET[routes_market.py<br/>Market Data]
            TRADING_R[routes_trading.py<br/>Trading]
            PAPER_R[routes_paper.py<br/>Paper Trading]
            NEWS_R[routes_news.py<br/>News]
            CHAT[routes_chat.py<br/>LLM Chat]
            WS_R[routes_websocket.py<br/>WebSocket]
        end
        
        subgraph "Core Services"
            CONFIG[config.py]
            SECURITY[security.py]
            LOGGING[logging.py]
        end
    end

    MAIN --> CORE
    MAIN --> AUTH_R
    MAIN --> MARKET
    MAIN --> TRADING_R
    MAIN --> PAPER_R
    MAIN --> NEWS_R
    MAIN --> CHAT
    MAIN --> WS_R
    
    CORE --> CONFIG
    AUTH_R --> SECURITY
    MAIN --> LOGGING
```

### Service Layer

```mermaid
graph TB
    subgraph "API Layer"
        ROUTES[Route Handlers]
    end

    subgraph "Service Layer"
        PROVIDER_FACTORY[Provider Factory]
        SCREENER[Screener Service]
        NEWS_SVC[News Service]
        FILINGS[Filings Service]
    end

    subgraph "Provider Chain"
        POLYGON_P[Polygon Provider]
        ALPACA_P[Alpaca Provider]
        YFINANCE_P[YFinance Provider]
    end

    subgraph "Paper Trading"
        ENGINE[Paper Engine]
        BROKER[Paper Broker]
        LEARNER[ML Learner]
        FEATURES[Feature Engine]
    end

    ROUTES --> PROVIDER_FACTORY
    ROUTES --> SCREENER
    ROUTES --> NEWS_SVC
    ROUTES --> ENGINE

    PROVIDER_FACTORY --> POLYGON_P
    PROVIDER_FACTORY --> ALPACA_P
    PROVIDER_FACTORY --> YFINANCE_P

    SCREENER --> PROVIDER_FACTORY
    
    ENGINE --> BROKER
    ENGINE --> LEARNER
    LEARNER --> FEATURES
```

---

## Frontend Architecture

### Component Hierarchy

```mermaid
graph TB
    subgraph "Next.js App Router"
        LAYOUT[layout.tsx]
        
        subgraph "Pages"
            HOME[/ Dashboard]
            MARKET_P[/market]
            TRADING_P[/trading]
            PORTFOLIO[/portfolio]
            PAPER_P[/paper-trading]
            NEWS_P[/news]
            CHAT_P[/chat]
        end
    end

    subgraph "Components"
        DASHBOARD[AdvancedDashboard]
        CHARTS[Chart Components]
        CARDS[Ticker Cards]
        SIDEBAR[Sidebar]
        MODALS[Modal Components]
    end

    subgraph "Services"
        API_SVC[API Service]
        AUTH_SVC[Auth Service]
        WS_SVC[WebSocket Service]
    end

    subgraph "State"
        ZUSTAND[Zustand Stores]
        QUERY[React Query]
    end

    LAYOUT --> HOME
    LAYOUT --> MARKET_P
    LAYOUT --> TRADING_P
    
    HOME --> DASHBOARD
    DASHBOARD --> CHARTS
    DASHBOARD --> CARDS
    
    CARDS --> API_SVC
    CHARTS --> WS_SVC
    
    API_SVC --> ZUSTAND
    WS_SVC --> QUERY
```

### State Management

```mermaid
graph LR
    subgraph "Zustand Stores"
        AUTH_STORE[Auth Store]
        MARKET_STORE[Market Store]
        TRADING_STORE[Trading Store]
        UI_STORE[UI Store]
    end

    subgraph "React Query"
        MARKET_QUERY[Market Queries]
        NEWS_QUERY[News Queries]
        TRADING_QUERY[Trading Queries]
    end

    subgraph "Components"
        COMP[React Components]
    end

    COMP --> AUTH_STORE
    COMP --> MARKET_STORE
    COMP --> TRADING_STORE
    COMP --> UI_STORE
    
    COMP --> MARKET_QUERY
    COMP --> NEWS_QUERY
    COMP --> TRADING_QUERY
```

---

## Data Flow

### Trading Signal Flow

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as FastAPI
    participant Screener as Screener
    participant Provider as Data Provider
    participant ML as ML Engine
    participant DB as Database

    UI->>API: GET /trade/screener
    API->>Screener: run_screener()
    Screener->>Provider: fetch_ohlc(tickers)
    Provider-->>Screener: OHLC DataFrame
    
    Screener->>Screener: Calculate indicators
    Screener->>ML: Generate signals
    ML-->>Screener: Signal + Confidence
    
    Screener-->>API: ScreenerResults
    API->>DB: Log signals
    API-->>UI: JSON Response
    
    UI->>UI: Display signals
```

### Paper Trade Execution

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as FastAPI
    participant Engine as Paper Engine
    participant Broker as Paper Broker
    participant Learner as ML Learner
    participant DB as Database

    UI->>API: POST /api/paper/runs
    API->>Engine: create_run()
    Engine->>DB: Insert PaperRun
    Engine-->>API: Run Created
    API-->>UI: Run ID

    loop Trading Loop
        Engine->>Engine: Generate Signal
        Engine->>Broker: Submit Order
        Broker->>Broker: Simulate Fill
        Broker->>DB: Record Trade
        
        Broker->>Learner: Trade Feedback
        Learner->>Learner: Update Model
        Learner->>DB: Save Snapshot
    end

    UI->>API: GET /api/paper/runs/{id}/stats
    API->>DB: Query Stats
    API-->>UI: Performance Metrics
```

### WebSocket Data Flow

```mermaid
sequenceDiagram
    participant Client as Browser
    participant WS as WebSocket Server
    participant Stream as Data Stream
    participant Provider as Market Provider

    Client->>WS: Connect /ws/market
    WS-->>Client: Connection ACK

    loop Real-time Updates
        Provider->>Stream: Price Update
        Stream->>WS: Broadcast
        WS-->>Client: JSON Message
        Client->>Client: Update UI
    end

    Client->>WS: Subscribe {symbols}
    WS->>Stream: Register Subscription
    
    Client->>WS: Disconnect
    WS->>Stream: Unsubscribe
```

---

## Trading System

### Paper Trading Architecture

```mermaid
graph TB
    subgraph "Paper Trading System"
        subgraph "Signal Generation"
            SCANNER[Market Scanner]
            THEORY[Trading Theories]
            FEATURES[Feature Engine]
        end

        subgraph "Execution"
            ENGINE[Paper Engine]
            BROKER[Paper Broker]
            RISK[Risk Manager]
        end

        subgraph "Learning"
            LEARNER[Online Learner]
            REPLAY[Replay Buffer]
            SNAPSHOT[Model Snapshots]
        end

        subgraph "Monitoring"
            HEALTH[Health Checks]
            METRICS[Performance Metrics]
            ALERTS[Alert System]
        end
    end

    SCANNER --> THEORY
    FEATURES --> THEORY
    THEORY --> ENGINE
    
    ENGINE --> RISK
    RISK --> BROKER
    
    BROKER --> LEARNER
    LEARNER --> REPLAY
    LEARNER --> SNAPSHOT
    
    ENGINE --> HEALTH
    ENGINE --> METRICS
    METRICS --> ALERTS
```

### Order Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Signal Generated
    PENDING --> SUBMITTED: Pass Risk Check
    PENDING --> REJECTED: Fail Risk Check
    
    SUBMITTED --> FILLED: Order Executed
    SUBMITTED --> PARTIAL: Partial Fill
    SUBMITTED --> FAILED: Execution Error
    
    PARTIAL --> FILLED: Complete
    PARTIAL --> CANCELLED: Cancel Remaining
    
    FILLED --> CLOSED: Position Closed
    CLOSED --> [*]
    
    REJECTED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

---

## Machine Learning Pipeline

### Online Learning System

```mermaid
graph TB
    subgraph "Data Collection"
        TRADES[Trade History]
        MARKET[Market Data]
        NEWS[News Sentiment]
    end

    subgraph "Feature Engineering"
        TECH[Technical Indicators]
        DERIVED[Derived Features]
        LABELS[Label Generation]
    end

    subgraph "Model Training"
        ONLINE[Online Learner]
        BATCH[Batch Trainer]
        EVAL[Model Evaluation]
    end

    subgraph "Inference"
        PREDICT[Signal Prediction]
        CONFIDENCE[Confidence Scoring]
        EXPLAIN[Explainability]
    end

    TRADES --> TECH
    MARKET --> TECH
    NEWS --> DERIVED
    
    TECH --> DERIVED
    DERIVED --> LABELS
    
    LABELS --> ONLINE
    LABELS --> BATCH
    
    ONLINE --> EVAL
    BATCH --> EVAL
    
    EVAL --> PREDICT
    PREDICT --> CONFIDENCE
    CONFIDENCE --> EXPLAIN
```

### RAG Pipeline

```mermaid
graph LR
    subgraph "Ingestion"
        PDF[PDF Documents]
        WEB[Web Content]
        RSS[RSS Feeds]
    end

    subgraph "Processing"
        CHUNK[Chunking]
        EMBED[Embedding]
        INDEX[Indexing]
    end

    subgraph "Storage"
        QDRANT[Qdrant Vector DB]
    end

    subgraph "Retrieval"
        QUERY[Query Processing]
        SEARCH[Semantic Search]
        CONTEXT[Context Assembly]
    end

    subgraph "Generation"
        LLM[LLM (OpenAI/Local)]
        RESPONSE[Response Generation]
    end

    PDF --> CHUNK
    WEB --> CHUNK
    RSS --> CHUNK
    
    CHUNK --> EMBED
    EMBED --> INDEX
    INDEX --> QDRANT
    
    QUERY --> SEARCH
    SEARCH --> QDRANT
    QDRANT --> CONTEXT
    
    CONTEXT --> LLM
    LLM --> RESPONSE
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    PaperRun ||--o{ Trade : contains
    PaperRun ||--o{ TheoryPerf : tracks
    PaperRun ||--o{ ModelSnapshot : stores
    
    Trade }o--|| TheoryPerf : belongs_to

    PaperRun {
        int id PK
        string name
        string status
        datetime started_at
        datetime ended_at
        float initial_balance
        float current_balance
        int total_trades
        float total_pnl
        float win_rate
        json config
    }

    Trade {
        int id PK
        string trade_id UK
        int paper_run_id FK
        string ticker
        string direction
        float quantity
        string theory_name
        string status
        datetime signal_time
        datetime fill_time
        float fill_price
        float realized_pnl
    }

    TheoryPerf {
        int id PK
        int paper_run_id FK
        string theory_name
        string theory_status
        float current_allocation
        int total_trades_executed
        float total_pnl
        float win_rate
        float sharpe_ratio
    }

    ModelSnapshot {
        int id PK
        int paper_run_id FK
        string model_name
        string model_type
        int version
        int samples_seen
        float training_accuracy
        float validation_accuracy
        float brier_score
        datetime created_at
    }
```

---

## Deployment Architecture

### Docker Compose Stack

```mermaid
graph TB
    subgraph "Docker Network"
        subgraph "Application"
            FRONTEND[ziggy-frontend<br/>:5173]
            BACKEND[ziggy-backend<br/>:8000]
        end

        subgraph "Data Services"
            POSTGRES[ziggy-postgres<br/>:5432]
            QDRANT[ziggy-qdrant<br/>:6333]
            REDIS[ziggy-redis<br/>:6379]
        end

        subgraph "Volumes"
            PG_DATA[pg_data]
            QDRANT_DATA[qdrant_storage]
            REDIS_DATA[redis_data]
        end
    end

    FRONTEND --> BACKEND
    BACKEND --> POSTGRES
    BACKEND --> QDRANT
    BACKEND --> REDIS
    
    POSTGRES --> PG_DATA
    QDRANT --> QDRANT_DATA
    REDIS --> REDIS_DATA
```

### Production Deployment

```mermaid
graph TB
    subgraph "CDN / Load Balancer"
        LB[Load Balancer]
    end

    subgraph "Application Tier"
        FE1[Frontend Instance 1]
        FE2[Frontend Instance 2]
        BE1[Backend Instance 1]
        BE2[Backend Instance 2]
    end

    subgraph "Data Tier"
        DB_PRIMARY[(Primary DB)]
        DB_REPLICA[(Read Replica)]
        CACHE[(Redis Cluster)]
        VECTOR[(Qdrant)]
    end

    subgraph "External"
        MARKET[Market Data APIs]
        LLM[LLM Provider]
    end

    LB --> FE1
    LB --> FE2
    FE1 --> BE1
    FE2 --> BE2
    
    BE1 --> DB_PRIMARY
    BE2 --> DB_PRIMARY
    BE1 --> DB_REPLICA
    BE2 --> DB_REPLICA
    
    BE1 --> CACHE
    BE2 --> CACHE
    BE1 --> VECTOR
    BE2 --> VECTOR
    
    BE1 --> MARKET
    BE1 --> LLM
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Authentication"
            JWT[JWT Tokens]
            API_KEY[API Keys]
            SESSION[Sessions]
        end

        subgraph "Authorization"
            RBAC[Role-Based Access]
            SCOPES[API Scopes]
        end

        subgraph "Protection"
            CORS[CORS Policy]
            RATE[Rate Limiting]
            CSRF[CSRF Protection]
        end

        subgraph "Data Security"
            ENCRYPT[Encryption]
            HASH[Password Hashing]
            SECRETS[Secret Management]
        end
    end

    JWT --> RBAC
    API_KEY --> SCOPES
    
    CORS --> RATE
    RATE --> CSRF
    
    ENCRYPT --> HASH
    HASH --> SECRETS
```

---

## Additional Resources

- [API Documentation](API.md)
- [Setup Guide](SetupGuide.md)
- [Deployment Guide](Deployment.md)
- [Full System Write-up](architecture/ZiggyAI_FULL_WRITEUP.md)
