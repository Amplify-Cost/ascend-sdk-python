// Package logger provides structured logging for the ASCEND ext_authz service.
//
// Supports JSON and text formats with configurable log levels.
// All logs include correlation IDs for distributed tracing.
//
// Author: ASCEND Platform Engineering
package logger

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"sync"
	"time"
)

// Level represents a log level.
type Level int

const (
	LevelDebug Level = iota
	LevelInfo
	LevelWarn
	LevelError
	LevelFatal
)

func (l Level) String() string {
	switch l {
	case LevelDebug:
		return "debug"
	case LevelInfo:
		return "info"
	case LevelWarn:
		return "warn"
	case LevelError:
		return "error"
	case LevelFatal:
		return "fatal"
	default:
		return "unknown"
	}
}

// ParseLevel converts a string to a Level.
func ParseLevel(s string) Level {
	switch strings.ToLower(s) {
	case "debug":
		return LevelDebug
	case "info":
		return LevelInfo
	case "warn", "warning":
		return LevelWarn
	case "error":
		return LevelError
	case "fatal":
		return LevelFatal
	default:
		return LevelInfo
	}
}

// Logger is a structured logger.
type Logger struct {
	mu       sync.Mutex
	level    Level
	format   string
	output   io.Writer
	fields   map[string]interface{}
}

// LogEntry represents a single log entry.
type LogEntry struct {
	Timestamp string                 `json:"timestamp"`
	Level     string                 `json:"level"`
	Message   string                 `json:"message"`
	Fields    map[string]interface{} `json:"fields,omitempty"`
}

var defaultLogger *Logger

func init() {
	defaultLogger = New(LevelInfo, "json", os.Stdout)
}

// New creates a new Logger.
func New(level Level, format string, output io.Writer) *Logger {
	return &Logger{
		level:  level,
		format: format,
		output: output,
		fields: make(map[string]interface{}),
	}
}

// Default returns the default logger.
func Default() *Logger {
	return defaultLogger
}

// SetDefault sets the default logger.
func SetDefault(l *Logger) {
	defaultLogger = l
}

// Configure configures the default logger.
func Configure(level, format string) {
	defaultLogger = New(ParseLevel(level), format, os.Stdout)
}

// WithField returns a new logger with an additional field.
func (l *Logger) WithField(key string, value interface{}) *Logger {
	newLogger := &Logger{
		level:  l.level,
		format: l.format,
		output: l.output,
		fields: make(map[string]interface{}),
	}
	for k, v := range l.fields {
		newLogger.fields[k] = v
	}
	newLogger.fields[key] = value
	return newLogger
}

// WithFields returns a new logger with additional fields.
func (l *Logger) WithFields(fields map[string]interface{}) *Logger {
	newLogger := &Logger{
		level:  l.level,
		format: l.format,
		output: l.output,
		fields: make(map[string]interface{}),
	}
	for k, v := range l.fields {
		newLogger.fields[k] = v
	}
	for k, v := range fields {
		newLogger.fields[k] = v
	}
	return newLogger
}

func (l *Logger) log(level Level, msg string, args ...interface{}) {
	if level < l.level {
		return
	}

	// Parse key-value pairs from args
	fields := make(map[string]interface{})
	for k, v := range l.fields {
		fields[k] = v
	}
	for i := 0; i < len(args)-1; i += 2 {
		if key, ok := args[i].(string); ok {
			fields[key] = args[i+1]
		}
	}

	l.mu.Lock()
	defer l.mu.Unlock()

	if l.format == "json" {
		entry := LogEntry{
			Timestamp: time.Now().UTC().Format(time.RFC3339Nano),
			Level:     level.String(),
			Message:   msg,
			Fields:    fields,
		}
		data, _ := json.Marshal(entry)
		fmt.Fprintln(l.output, string(data))
	} else {
		// Text format
		fieldStr := ""
		for k, v := range fields {
			fieldStr += fmt.Sprintf(" %s=%v", k, v)
		}
		fmt.Fprintf(l.output, "%s [%s] %s%s\n",
			time.Now().UTC().Format(time.RFC3339),
			strings.ToUpper(level.String()),
			msg,
			fieldStr,
		)
	}
}

// Debug logs at debug level.
func (l *Logger) Debug(msg string, args ...interface{}) {
	l.log(LevelDebug, msg, args...)
}

// Info logs at info level.
func (l *Logger) Info(msg string, args ...interface{}) {
	l.log(LevelInfo, msg, args...)
}

// Warn logs at warn level.
func (l *Logger) Warn(msg string, args ...interface{}) {
	l.log(LevelWarn, msg, args...)
}

// Error logs at error level.
func (l *Logger) Error(msg string, args ...interface{}) {
	l.log(LevelError, msg, args...)
}

// Fatal logs at fatal level and exits.
func (l *Logger) Fatal(msg string, args ...interface{}) {
	l.log(LevelFatal, msg, args...)
	os.Exit(1)
}

// Package-level convenience functions

// Debug logs at debug level using the default logger.
func Debug(msg string, args ...interface{}) {
	defaultLogger.Debug(msg, args...)
}

// Info logs at info level using the default logger.
func Info(msg string, args ...interface{}) {
	defaultLogger.Info(msg, args...)
}

// Warn logs at warn level using the default logger.
func Warn(msg string, args ...interface{}) {
	defaultLogger.Warn(msg, args...)
}

// Error logs at error level using the default logger.
func Error(msg string, args ...interface{}) {
	defaultLogger.Error(msg, args...)
}

// Fatal logs at fatal level using the default logger and exits.
func Fatal(msg string, args ...interface{}) {
	defaultLogger.Fatal(msg, args...)
}
