# Kawaflow Product Overview

Kawaflow is a container orchestration and workflow management system built around event-driven architecture. The system consists of two main components:

## Core Components

**Flow Engine** - An actor-based event processing system that handles workflow orchestration using a custom framework called "Kawa". Supports cron-based scheduling, email notifications, and weather data integration.

**Flow Manager** - A WebSocket-based service for managing Docker container lifecycles. Provides real-time container management capabilities including start, stop, and monitoring operations.

## Key Features

- Event-driven actor system with custom event types
- Docker container lifecycle management
- WebSocket-based real-time communication
- Automatic port assignment for containers
- Cron-based task scheduling
- Email notification system

## Current Status

The project is in early development with basic container management and workflow capabilities implemented. Future plans include Laravel app integration, timeout/interval events, and code generation features.
