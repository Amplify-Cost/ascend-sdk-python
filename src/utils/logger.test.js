import { describe, it, expect } from 'vitest';
import logger from './logger';

describe('Enterprise Logger', () => {
  it('should exist', () => {
    expect(logger).toBeDefined();
    expect(logger.debug).toBeInstanceOf(Function);
    expect(logger.info).toBeInstanceOf(Function);
    expect(logger.warn).toBeInstanceOf(Function);
    expect(logger.error).toBeInstanceOf(Function);
  });
});
