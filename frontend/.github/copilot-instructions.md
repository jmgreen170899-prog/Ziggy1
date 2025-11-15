This is the ZiggyClean Frontend project - a comprehensive financial trading and market analysis platform.

## Project Overview

This Next.js application provides a modern, real-time trading interface with the following key features:

- **Real-time Market Data**: Live quotes, charts, and market analysis
- **Trading Signals**: AI-generated trading recommendations with confidence scores
- **Portfolio Management**: Complete portfolio tracking and performance analytics
- **News Integration**: Real-time financial news with sentiment analysis
- **Cryptocurrency Tracking**: Crypto price monitoring and technical analysis
- **Alert System**: Customizable price and condition alerts
- **Learning System**: AI adaptation based on user feedback

## Technical Architecture

- **Frontend Framework**: Next.js 15.5.6 with TypeScript and App Router
- **State Management**: Zustand stores with persistence
- **Styling**: Tailwind CSS with dark theme support
- **Real-time Communication**: Socket.IO for WebSocket connections
- **API Integration**: Axios client with comprehensive backend integration
- **Component Library**: Custom UI components built with accessibility in mind

## Key Components

- `Dashboard.tsx` - Main dashboard with portfolio overview and real-time data
- `QuoteCard.tsx` - Market data display components
- `SignalsList.tsx` - Trading signal management and display
- `Sidebar.tsx` - Navigation and layout management

## Backend Integration

The frontend integrates with a comprehensive backend API that provides:

- RAG query system for AI-powered financial analysis
- Real-time market data and WebSocket updates
- Trading signal generation and portfolio management
- News aggregation with sentiment analysis
- Alert management and notification systems
- Learning and adaptation capabilities

## Development Guidelines

When working on this project:

1. Follow TypeScript best practices and maintain type safety
2. Use the existing Zustand stores for state management
3. Implement real-time features using the WebSocket service
4. Follow the established component patterns for consistency
5. Ensure accessibility in all UI components
6. Test WebSocket connections and API integrations thoroughly

## File Structure

The project follows a modular structure with clear separation of concerns:

- `app/` - Next.js App Router pages and layouts
- `components/` - Reusable React components organized by feature
- `services/` - External service integrations (API, WebSocket)
- `store/` - Zustand state management stores
- `hooks/` - Custom React hooks for data fetching and real-time updates
- `types/` - TypeScript type definitions
- `utils/` - Utility functions and helpers
