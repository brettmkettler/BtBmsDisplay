# Overview

This is a real-time battery monitoring system designed to display status information for 8 batteries using a fullstack React/Express application. The system provides a live dashboard with battery metrics including voltage, amperage, and charge levels. It's built with a modern TypeScript stack featuring React on the frontend, Express on the backend, and WebSocket integration for real-time updates. The application uses a dark theme with retro display aesthetics optimized for touch interfaces and high-resolution screens.

# User Preferences

Preferred communication style: Simple, everyday language.
#
# System Architecture

## Frontend Architecture
- **Framework**: React 18 with TypeScript and Vite for development
- **UI Library**: Shadcn/UI components built on Radix UI primitives
- **Styling**: Tailwind CSS with custom battery-themed color palette (red, yellow, green)
- **State Management**: TanStack Query for server state, React hooks for local state
- **Routing**: Wouter for client-side routing
- **Real-time Communication**: Native WebSocket API with custom hook for connection management

## Backend Architecture
- **Framework**: Express.js with TypeScript
- **Runtime**: Node.js with ES modules
- **Real-time**: WebSocket server using 'ws' library for live battery updates
- **Development**: TSX for TypeScript execution in development
- **Build**: ESBuild for production bundling

## Data Storage
- **ORM**: Drizzle ORM with PostgreSQL dialect configuration
- **Database**: Configured for PostgreSQL via Neon Database serverless
- **Schema**: Structured battery data table with voltage, amperage, charge level, and timestamps
- **Development Storage**: In-memory storage implementation for development/testing

## Authentication and Authorization
- **Session Management**: PostgreSQL session store using connect-pg-simple
- **Current State**: Basic session infrastructure in place, specific auth mechanisms not yet implemented

## External Dependencies
- **Database Provider**: Neon Database (PostgreSQL serverless)
- **UI Components**: Radix UI ecosystem for accessible, unstyled components
- **Real-time**: WebSocket protocol for bidirectional client-server communication
- **Styling**: Tailwind CSS with PostCSS processing
- **Development**: Replit-specific plugins for development environment integration