/**
 * SEC-054: OW-AI SDK Request/Response Interceptors
 * =================================================
 *
 * Middleware pattern for SDK requests and responses.
 * Aligned with Axios interceptor pattern for familiarity.
 *
 * Features:
 * - Request modification before send
 * - Response transformation after receive
 * - Error interception and handling
 * - Request ID generation
 * - Custom header injection
 * - Logging hooks
 *
 * Compliance: SOC 2 CC6.1, NIST SI-4
 */

/**
 * Request configuration object
 */
export interface RequestConfig {
  /** HTTP method */
  method: string;
  /** Request URL */
  url: string;
  /** Request headers */
  headers: Record<string, string>;
  /** Request body data */
  data?: Record<string, unknown>;
  /** URL parameters */
  params?: Record<string, unknown>;
  /** Request timestamp */
  timestamp: Date;
  /** Unique request ID */
  requestId: string;
  /** Custom metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Response object
 */
export interface ResponseData {
  /** Response status code */
  status: number;
  /** Response headers */
  headers: Record<string, string>;
  /** Response body data */
  data: Record<string, unknown>;
  /** Original request config */
  config: RequestConfig;
  /** Response duration in ms */
  duration: number;
}

/**
 * Error object for interceptors
 */
export interface InterceptorError {
  /** Error message */
  message: string;
  /** Error code */
  code?: string;
  /** HTTP status code */
  status?: number;
  /** Original request config */
  config: RequestConfig;
  /** Response data if available */
  response?: ResponseData;
}

/**
 * Request interceptor function
 */
export type RequestInterceptor = (
  config: RequestConfig
) => RequestConfig | Promise<RequestConfig>;

/**
 * Response interceptor function
 */
export type ResponseInterceptor = (
  response: ResponseData
) => ResponseData | Promise<ResponseData>;

/**
 * Error interceptor function
 */
export type ErrorInterceptor = (
  error: InterceptorError
) => InterceptorError | Promise<InterceptorError>;

/**
 * Interceptor entry with fulfilled and rejected handlers
 */
interface InterceptorEntry<T, E> {
  id: number;
  fulfilled?: T;
  rejected?: E;
}

/**
 * SEC-054: Interceptor Manager
 *
 * Manages request and response interceptors for the SDK client.
 *
 * @example
 * ```typescript
 * const interceptors = new InterceptorManager();
 *
 * // Add request interceptor for request IDs
 * interceptors.request.use((config) => {
 *   config.headers['X-Request-ID'] = generateUUID();
 *   return config;
 * });
 *
 * // Add response interceptor for logging
 * interceptors.response.use((response) => {
 *   console.log(`[${response.config.method}] ${response.config.url} - ${response.status}`);
 *   return response;
 * });
 *
 * // Add error interceptor
 * interceptors.response.use(undefined, (error) => {
 *   console.error(`Request failed: ${error.message}`);
 *   return error;
 * });
 * ```
 */
export class InterceptorManager {
  /** Request interceptors */
  readonly request: InterceptorChain<RequestInterceptor, ErrorInterceptor>;
  /** Response interceptors */
  readonly response: InterceptorChain<ResponseInterceptor, ErrorInterceptor>;

  constructor() {
    this.request = new InterceptorChain<RequestInterceptor, ErrorInterceptor>();
    this.response = new InterceptorChain<ResponseInterceptor, ErrorInterceptor>();
  }

  /**
   * Run all request interceptors
   */
  async runRequestInterceptors(config: RequestConfig): Promise<RequestConfig> {
    let result = config;
    for (const interceptor of this.request.getAll()) {
      if (interceptor.fulfilled) {
        try {
          result = await interceptor.fulfilled(result);
        } catch (error) {
          if (interceptor.rejected) {
            const interceptorError: InterceptorError = {
              message: error instanceof Error ? error.message : String(error),
              config: result,
            };
            await interceptor.rejected(interceptorError);
          }
          throw error;
        }
      }
    }
    return result;
  }

  /**
   * Run all response interceptors
   */
  async runResponseInterceptors(response: ResponseData): Promise<ResponseData> {
    let result = response;
    for (const interceptor of this.response.getAll()) {
      if (interceptor.fulfilled) {
        try {
          result = await interceptor.fulfilled(result);
        } catch (error) {
          if (interceptor.rejected) {
            const interceptorError: InterceptorError = {
              message: error instanceof Error ? error.message : String(error),
              config: response.config,
              response: result,
            };
            await interceptor.rejected(interceptorError);
          }
          throw error;
        }
      }
    }
    return result;
  }

  /**
   * Run error interceptors
   */
  async runErrorInterceptors(error: InterceptorError): Promise<InterceptorError> {
    let result = error;
    for (const interceptor of this.response.getAll()) {
      if (interceptor.rejected) {
        result = await interceptor.rejected(result);
      }
    }
    return result;
  }

  /**
   * Clear all interceptors
   */
  clear(): void {
    this.request.clear();
    this.response.clear();
  }
}

/**
 * Individual interceptor chain
 */
export class InterceptorChain<T, E> {
  private interceptors: InterceptorEntry<T, E>[] = [];
  private idCounter = 0;

  /**
   * Add an interceptor
   *
   * @param fulfilled - Success handler
   * @param rejected - Error handler
   * @returns Interceptor ID for removal
   */
  use(fulfilled?: T, rejected?: E): number {
    const id = ++this.idCounter;
    this.interceptors.push({ id, fulfilled, rejected });
    return id;
  }

  /**
   * Remove an interceptor by ID
   *
   * @param id - Interceptor ID
   * @returns True if removed
   */
  eject(id: number): boolean {
    const index = this.interceptors.findIndex((i) => i.id === id);
    if (index > -1) {
      this.interceptors.splice(index, 1);
      return true;
    }
    return false;
  }

  /**
   * Get all interceptors
   */
  getAll(): InterceptorEntry<T, E>[] {
    return [...this.interceptors];
  }

  /**
   * Clear all interceptors
   */
  clear(): void {
    this.interceptors = [];
  }

  /**
   * Get interceptor count
   */
  get length(): number {
    return this.interceptors.length;
  }
}

/**
 * Generate a unique request ID
 */
export function generateRequestId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return `req_${timestamp}_${random}`;
}

/**
 * Built-in interceptor: Add request ID to all requests
 */
export const requestIdInterceptor: RequestInterceptor = (config) => {
  config.headers['X-Request-ID'] = config.requestId || generateRequestId();
  return config;
};

/**
 * Built-in interceptor: Add timestamp to all requests
 */
export const timestampInterceptor: RequestInterceptor = (config) => {
  config.headers['X-Request-Time'] = config.timestamp.toISOString();
  return config;
};

/**
 * Built-in interceptor: Log all requests (debug mode)
 */
export const debugLogInterceptor: RequestInterceptor = (config) => {
  console.log(`[OWKAI] ${config.method.toUpperCase()} ${config.url}`, {
    requestId: config.requestId,
    timestamp: config.timestamp,
  });
  return config;
};

/**
 * Built-in interceptor: Log response timing
 */
export const responseTimingInterceptor: ResponseInterceptor = (response) => {
  console.log(
    `[OWKAI] ${response.config.method.toUpperCase()} ${response.config.url} - ${response.status} (${response.duration}ms)`
  );
  return response;
};
