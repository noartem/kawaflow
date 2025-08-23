# Kawaflow Product Overview

Kawaflow is a container orchestration and workflow management system built around event-driven architecture. The system consists of three main components:

## Core Components

**Kawa Framework** - A standalone Python package providing a custom actor-based event processing system. Handles workflow orchestration with support for cron-based scheduling, email notifications, and extensible event types. Can be used independently or integrated into other applications.

**Flow Examples** - Example implementations and test scripts demonstrating Kawa framework usage. Includes weather data integration examples and framework validation tests.

**Flow Manager** - A WebSocket-based service for managing Docker container lifecycles. Provides real-time container management capabilities including start, stop, and monitoring operations.

## Key Features

- Event-driven actor system with custom event types
- Docker container lifecycle management
- WebSocket-based real-time communication
- Automatic port assignment for containers
- Cron-based task scheduling
- Email notification system

## Current Status

The project is in early development with:

**Implemented:**
- Kawa framework core actor system
- Basic event types (Cron, Email)
- Flow-manager container lifecycle management
- Docker integration and containerized development
- Example implementations and testing

**Planned Features:**
- Laravel app integration
- Timeout/interval events
- Webhook support
- Code generation features
- PyPI package publication for Kawa framework
- Docker Compose orchestration
- Local PyPI nexus for caching
