# Proposal: Refactor AI Provider with SSE Streaming

## Summary

Refactor skill-hub's AI provider system to adopt idone's proven LLM provider architecture, adding SSE streaming support, multi-provider configuration management, and improved separation of concerns.

## Problem

Current skill-hub AI implementation has several limitations:

1. **No Streaming Support**: Only synchronous `complete()` method, no real-time response streaming
2. **Basic Provider Interface**: Limited to single method, no validation or config schema support
3. **Poor Config Management**: Simple config model without structured validation
4. **No SSE Endpoints**: Web interface cannot stream AI responses progressively
5. **Tight Coupling**: Provider logic mixed with finder/translator logic

## Goals

1. **Add Streaming Interface**: `generate_stream()` method returning async generator
2. **Implement SSE Endpoints**: Server-Sent Events for web UI streaming
3. **Provider Config Schema**: Structured validation with field schemas per provider
4. **Improved Separation**: Clean separation between provider CRUD and AI operations
5. **Multi-Provider Support**: Easy addition of new providers (Anthropic, etc.)

## Approach

Adopt ido
