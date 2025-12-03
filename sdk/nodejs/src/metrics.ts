/**
 * SEC-054: OW-AI SDK Metrics Collection
 * =====================================
 *
 * Enterprise-grade metrics and telemetry for SDK operations.
 * Aligned with Datadog/Sentry SDK patterns.
 *
 * Features:
 * - Request/response latency tracking
 * - Error rate monitoring
 * - Success/failure counters
 * - Histogram data for latency distribution
 * - Event callbacks for external monitoring integration
 *
 * Compliance: SOC 2 CC6.1, NIST SI-4
 */

/**
 * Individual metric event
 */
export interface MetricEvent {
  /** Event type */
  type: 'request' | 'response' | 'error' | 'retry' | 'timeout';
  /** HTTP method */
  method: string;
  /** API endpoint */
  endpoint: string;
  /** Response status code */
  statusCode?: number;
  /** Request duration in milliseconds */
  duration: number;
  /** Timestamp */
  timestamp: Date;
  /** Error message if applicable */
  error?: string;
  /** Retry attempt number */
  retryAttempt?: number;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Aggregated metrics snapshot
 */
export interface MetricsSnapshot {
  /** Total requests made */
  totalRequests: number;
  /** Successful requests */
  successCount: number;
  /** Failed requests */
  errorCount: number;
  /** Timeout count */
  timeoutCount: number;
  /** Rate limited count */
  rateLimitCount: number;
  /** Retry count */
  retryCount: number;
  /** Average latency in ms */
  avgLatency: number;
  /** Min latency in ms */
  minLatency: number;
  /** Max latency in ms */
  maxLatency: number;
  /** P50 latency in ms */
  p50Latency: number;
  /** P95 latency in ms */
  p95Latency: number;
  /** P99 latency in ms */
  p99Latency: number;
  /** Success rate (0-1) */
  successRate: number;
  /** Error rate (0-1) */
  errorRate: number;
  /** Requests per minute (based on window) */
  requestsPerMinute: number;
  /** Time window start */
  windowStart: Date;
  /** Time window end */
  windowEnd: Date;
  /** Breakdown by endpoint */
  byEndpoint: Record<string, EndpointMetrics>;
  /** Breakdown by status code */
  byStatusCode: Record<number, number>;
}

/**
 * Per-endpoint metrics
 */
export interface EndpointMetrics {
  requests: number;
  errors: number;
  avgLatency: number;
  successRate: number;
}

/**
 * Metrics event callback
 */
export type MetricsCallback = (event: MetricEvent) => void;

/**
 * SEC-054: Metrics Collector
 *
 * Collects and aggregates SDK performance metrics.
 * Supports external monitoring integration via callbacks.
 *
 * @example
 * ```typescript
 * const metrics = new MetricsCollector({ maxEvents: 1000 });
 *
 * // Register callback for real-time monitoring
 * metrics.onEvent((event) => {
 *   datadogClient.gauge('owkai.sdk.latency', event.duration);
 * });
 *
 * // Record events
 * metrics.recordRequest('POST', '/api/authorization/agent-action', 150, 200);
 *
 * // Get snapshot
 * const snapshot = metrics.getSnapshot();
 * console.log(`Success rate: ${snapshot.successRate * 100}%`);
 * ```
 */
export class MetricsCollector {
  private events: MetricEvent[] = [];
  private callbacks: MetricsCallback[] = [];
  private readonly maxEvents: number;
  private readonly windowMs: number;

  /**
   * Initialize metrics collector
   *
   * @param options - Configuration options
   */
  constructor(options: { maxEvents?: number; windowMs?: number } = {}) {
    this.maxEvents = options.maxEvents || 10000;
    this.windowMs = options.windowMs || 300000; // 5 minutes default
  }

  /**
   * Register callback for metric events
   *
   * @param callback - Function to call on each metric event
   * @returns Unsubscribe function
   */
  onEvent(callback: MetricsCallback): () => void {
    this.callbacks.push(callback);
    return () => {
      const index = this.callbacks.indexOf(callback);
      if (index > -1) {
        this.callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Record a request event
   */
  recordRequest(
    method: string,
    endpoint: string,
    duration: number,
    statusCode?: number,
    metadata?: Record<string, unknown>
  ): void {
    const event: MetricEvent = {
      type: 'request',
      method,
      endpoint,
      duration,
      statusCode,
      timestamp: new Date(),
      metadata,
    };

    this.addEvent(event);
  }

  /**
   * Record an error event
   */
  recordError(
    method: string,
    endpoint: string,
    duration: number,
    error: string,
    statusCode?: number
  ): void {
    const event: MetricEvent = {
      type: 'error',
      method,
      endpoint,
      duration,
      statusCode,
      timestamp: new Date(),
      error,
    };

    this.addEvent(event);
  }

  /**
   * Record a timeout event
   */
  recordTimeout(method: string, endpoint: string, duration: number): void {
    const event: MetricEvent = {
      type: 'timeout',
      method,
      endpoint,
      duration,
      timestamp: new Date(),
    };

    this.addEvent(event);
  }

  /**
   * Record a retry event
   */
  recordRetry(
    method: string,
    endpoint: string,
    retryAttempt: number,
    reason: string
  ): void {
    const event: MetricEvent = {
      type: 'retry',
      method,
      endpoint,
      duration: 0,
      timestamp: new Date(),
      retryAttempt,
      error: reason,
    };

    this.addEvent(event);
  }

  /**
   * Add event to collection and notify callbacks
   */
  private addEvent(event: MetricEvent): void {
    this.events.push(event);

    // Trim old events if exceeding max
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }

    // Notify callbacks
    for (const callback of this.callbacks) {
      try {
        callback(event);
      } catch (err) {
        // Don't let callback errors break the SDK
        console.error('[OWKAI Metrics] Callback error:', err);
      }
    }
  }

  /**
   * Get metrics snapshot for current window
   */
  getSnapshot(): MetricsSnapshot {
    const now = new Date();
    const windowStart = new Date(now.getTime() - this.windowMs);

    // Filter events within window
    const windowEvents = this.events.filter(
      (e) => e.timestamp >= windowStart
    );

    const requests = windowEvents.filter(
      (e) => e.type === 'request' || e.type === 'error'
    );
    const errors = windowEvents.filter((e) => e.type === 'error');
    const timeouts = windowEvents.filter((e) => e.type === 'timeout');
    const rateLimits = windowEvents.filter(
      (e) => e.statusCode === 429
    );
    const retries = windowEvents.filter((e) => e.type === 'retry');

    // Calculate latencies
    const latencies = requests
      .map((e) => e.duration)
      .filter((d) => d > 0)
      .sort((a, b) => a - b);

    const avgLatency =
      latencies.length > 0
        ? latencies.reduce((a, b) => a + b, 0) / latencies.length
        : 0;

    // Calculate percentiles
    const percentile = (arr: number[], p: number): number => {
      if (arr.length === 0) return 0;
      const index = Math.ceil((p / 100) * arr.length) - 1;
      return arr[Math.max(0, index)];
    };

    // Group by endpoint
    const byEndpoint: Record<string, EndpointMetrics> = {};
    for (const event of requests) {
      if (!byEndpoint[event.endpoint]) {
        byEndpoint[event.endpoint] = {
          requests: 0,
          errors: 0,
          avgLatency: 0,
          successRate: 0,
        };
      }
      byEndpoint[event.endpoint].requests++;
      if (event.type === 'error') {
        byEndpoint[event.endpoint].errors++;
      }
    }

    // Calculate per-endpoint metrics
    for (const endpoint of Object.keys(byEndpoint)) {
      const endpointEvents = requests.filter((e) => e.endpoint === endpoint);
      const endpointLatencies = endpointEvents.map((e) => e.duration);
      byEndpoint[endpoint].avgLatency =
        endpointLatencies.length > 0
          ? endpointLatencies.reduce((a, b) => a + b, 0) / endpointLatencies.length
          : 0;
      byEndpoint[endpoint].successRate =
        byEndpoint[endpoint].requests > 0
          ? (byEndpoint[endpoint].requests - byEndpoint[endpoint].errors) /
            byEndpoint[endpoint].requests
          : 0;
    }

    // Group by status code
    const byStatusCode: Record<number, number> = {};
    for (const event of requests) {
      if (event.statusCode) {
        byStatusCode[event.statusCode] = (byStatusCode[event.statusCode] || 0) + 1;
      }
    }

    // Calculate requests per minute
    const windowMinutes = this.windowMs / 60000;
    const requestsPerMinute = requests.length / windowMinutes;

    return {
      totalRequests: requests.length,
      successCount: requests.length - errors.length,
      errorCount: errors.length,
      timeoutCount: timeouts.length,
      rateLimitCount: rateLimits.length,
      retryCount: retries.length,
      avgLatency: Math.round(avgLatency),
      minLatency: latencies.length > 0 ? Math.min(...latencies) : 0,
      maxLatency: latencies.length > 0 ? Math.max(...latencies) : 0,
      p50Latency: Math.round(percentile(latencies, 50)),
      p95Latency: Math.round(percentile(latencies, 95)),
      p99Latency: Math.round(percentile(latencies, 99)),
      successRate: requests.length > 0 ? (requests.length - errors.length) / requests.length : 0,
      errorRate: requests.length > 0 ? errors.length / requests.length : 0,
      requestsPerMinute: Math.round(requestsPerMinute * 100) / 100,
      windowStart,
      windowEnd: now,
      byEndpoint,
      byStatusCode,
    };
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.events = [];
  }

  /**
   * Get raw events (for debugging)
   */
  getEvents(): MetricEvent[] {
    return [...this.events];
  }
}
