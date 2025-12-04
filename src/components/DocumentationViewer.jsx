/**
 * Ascend Documentation Viewer
 *
 * Enterprise-grade documentation viewer with security-first design.
 * Provides secure markdown rendering, search functionality, and navigation.
 *
 * Security Features:
 * - XSS Prevention: No dangerouslySetInnerHTML, all content sanitized
 * - Input Validation: Search queries sanitized and length-limited
 * - HTTPS Only: All API calls via authenticated endpoints
 * - Multi-tenant: Organization-scoped documentation access
 *
 * Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312
 *
 * Document ID: ASCEND-DOCS-VIEWER-001
 * Author: Ascend Engineering Team
 * Publisher: OW-kai Technologies Inc.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { API_BASE_URL } from '../config/api';
import { fetchWithAuth } from '../utils/fetchWithAuth';

// Security: Maximum search query length to prevent abuse
const MAX_SEARCH_LENGTH = 100;

// Security: Allowed markdown patterns (whitelist approach)
const SAFE_HEADING_PATTERN = /^(#{1,6})\s+(.+)$/;
const SAFE_LIST_PATTERN = /^(\s*)[-*]\s+(.+)$/;
const SAFE_ORDERED_LIST_PATTERN = /^(\s*)\d+\.\s+(.+)$/;
const SAFE_CODE_BLOCK_START = /^```(\w*)$/;
const SAFE_CODE_BLOCK_END = /^```$/;
const SAFE_INLINE_CODE = /`([^`]+)`/g;
const SAFE_BOLD = /\*\*([^*]+)\*\*/g;
const SAFE_ITALIC = /\*([^*]+)\*/g;
const SAFE_LINK = /\[([^\]]+)\]\(([^)]+)\)/g;
const SAFE_TABLE_ROW = /^\|(.+)\|$/;

/**
 * Secure text sanitizer - removes any potential XSS vectors
 * @param {string} text - Raw text to sanitize
 * @returns {string} - Sanitized text safe for rendering
 */
const sanitizeText = (text) => {
  if (typeof text !== 'string') return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

/**
 * Secure URL validator - only allows safe protocols
 * @param {string} url - URL to validate
 * @returns {boolean} - Whether URL is safe
 */
const isSecureUrl = (url) => {
  if (typeof url !== 'string') return false;
  const trimmed = url.trim().toLowerCase();
  // Only allow https, mailto, and relative paths
  return trimmed.startsWith('https://') ||
         trimmed.startsWith('mailto:') ||
         trimmed.startsWith('/') ||
         trimmed.startsWith('#') ||
         (!trimmed.includes(':'));
};

/**
 * Parse inline markdown elements securely
 * @param {string} text - Text with inline markdown
 * @param {boolean} isDarkMode - Theme mode
 * @returns {Array} - Array of React elements
 */
const parseInlineElements = (text, isDarkMode) => {
  if (!text) return [];

  const elements = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Check for inline code
    const codeMatch = remaining.match(/`([^`]+)`/);
    // Check for bold
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    // Check for italic (single asterisk, not part of bold)
    const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);
    // Check for link
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);

    // Find earliest match
    let earliest = null;
    let earliestIndex = remaining.length;

    if (codeMatch && codeMatch.index < earliestIndex) {
      earliest = { type: 'code', match: codeMatch };
      earliestIndex = codeMatch.index;
    }
    if (boldMatch && boldMatch.index < earliestIndex) {
      earliest = { type: 'bold', match: boldMatch };
      earliestIndex = boldMatch.index;
    }
    if (italicMatch && italicMatch.index < earliestIndex) {
      earliest = { type: 'italic', match: italicMatch };
      earliestIndex = italicMatch.index;
    }
    if (linkMatch && linkMatch.index < earliestIndex) {
      earliest = { type: 'link', match: linkMatch };
      earliestIndex = linkMatch.index;
    }

    if (!earliest) {
      // No more matches, add remaining text
      if (remaining) {
        elements.push(<span key={key++}>{remaining}</span>);
      }
      break;
    }

    // Add text before match
    if (earliestIndex > 0) {
      elements.push(<span key={key++}>{remaining.substring(0, earliestIndex)}</span>);
    }

    // Add matched element
    const { type, match } = earliest;
    switch (type) {
      case 'code':
        elements.push(
          <code
            key={key++}
            className={`px-1.5 py-0.5 rounded font-mono text-sm ${
              isDarkMode
                ? 'bg-slate-700 text-emerald-400'
                : 'bg-gray-100 text-emerald-600'
            }`}
          >
            {match[1]}
          </code>
        );
        break;
      case 'bold':
        elements.push(<strong key={key++} className="font-semibold">{match[1]}</strong>);
        break;
      case 'italic':
        elements.push(<em key={key++} className="italic">{match[1]}</em>);
        break;
      case 'link':
        if (isSecureUrl(match[2])) {
          elements.push(
            <a
              key={key++}
              href={match[2]}
              target={match[2].startsWith('http') ? '_blank' : undefined}
              rel={match[2].startsWith('http') ? 'noopener noreferrer' : undefined}
              className={`underline hover:no-underline ${
                isDarkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'
              }`}
            >
              {match[1]}
            </a>
          );
        } else {
          // Unsafe URL - render as plain text
          elements.push(<span key={key++}>[{match[1]}]</span>);
        }
        break;
    }

    remaining = remaining.substring(earliestIndex + match[0].length);
  }

  return elements;
};

/**
 * Secure Markdown Renderer Component
 * Converts markdown to React elements without using dangerouslySetInnerHTML
 */
const SecureMarkdownRenderer = ({ content, isDarkMode, searchQuery = '' }) => {
  const elements = useMemo(() => {
    if (!content || typeof content !== 'string') return [];

    const lines = content.split('\n');
    const rendered = [];
    let key = 0;
    let inCodeBlock = false;
    let codeBlockContent = [];
    let codeBlockLanguage = '';
    let inTable = false;
    let tableRows = [];
    let tableHeaders = [];

    const highlightSearch = (text) => {
      if (!searchQuery || searchQuery.length < 2) return text;

      const query = searchQuery.toLowerCase();
      const lowerText = text.toLowerCase();
      const index = lowerText.indexOf(query);

      if (index === -1) return text;

      return (
        <>
          {text.substring(0, index)}
          <mark className={`px-0.5 rounded ${isDarkMode ? 'bg-yellow-500/40 text-yellow-200' : 'bg-yellow-200 text-yellow-900'}`}>
            {text.substring(index, index + searchQuery.length)}
          </mark>
          {text.substring(index + searchQuery.length)}
        </>
      );
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Handle code blocks
      if (SAFE_CODE_BLOCK_START.test(line) && !inCodeBlock) {
        inCodeBlock = true;
        codeBlockLanguage = line.match(SAFE_CODE_BLOCK_START)[1] || 'text';
        codeBlockContent = [];
        continue;
      }

      if (SAFE_CODE_BLOCK_END.test(line) && inCodeBlock) {
        inCodeBlock = false;
        rendered.push(
          <pre
            key={key++}
            className={`p-4 rounded-lg overflow-x-auto my-4 font-mono text-sm ${
              isDarkMode
                ? 'bg-slate-900 text-slate-300 border border-slate-700'
                : 'bg-gray-900 text-gray-100'
            }`}
          >
            <code>{codeBlockContent.join('\n')}</code>
          </pre>
        );
        codeBlockContent = [];
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      // Handle tables
      if (SAFE_TABLE_ROW.test(line)) {
        const cells = line.split('|').filter(c => c.trim() !== '');

        // Check if this is a separator row (---|---|---)
        if (cells.every(c => /^[\s-:]+$/.test(c))) {
          continue; // Skip separator row
        }

        if (!inTable) {
          inTable = true;
          tableHeaders = cells.map(c => c.trim());
          tableRows = [];
        } else {
          tableRows.push(cells.map(c => c.trim()));
        }

        // Check if next line is not a table row
        if (i + 1 >= lines.length || !SAFE_TABLE_ROW.test(lines[i + 1])) {
          // Render table
          rendered.push(
            <div key={key++} className="overflow-x-auto my-4">
              <table className={`min-w-full border-collapse ${
                isDarkMode ? 'border-slate-600' : 'border-gray-300'
              }`}>
                <thead>
                  <tr className={isDarkMode ? 'bg-slate-700' : 'bg-gray-100'}>
                    {tableHeaders.map((header, idx) => (
                      <th
                        key={idx}
                        className={`px-4 py-2 text-left font-semibold border ${
                          isDarkMode
                            ? 'border-slate-600 text-slate-200'
                            : 'border-gray-300 text-gray-700'
                        }`}
                      >
                        {highlightSearch(header)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row, rowIdx) => (
                    <tr
                      key={rowIdx}
                      className={rowIdx % 2 === 0
                        ? (isDarkMode ? 'bg-slate-800' : 'bg-white')
                        : (isDarkMode ? 'bg-slate-750' : 'bg-gray-50')
                      }
                    >
                      {row.map((cell, cellIdx) => (
                        <td
                          key={cellIdx}
                          className={`px-4 py-2 border ${
                            isDarkMode
                              ? 'border-slate-600 text-slate-300'
                              : 'border-gray-300 text-gray-600'
                          }`}
                        >
                          {highlightSearch(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          inTable = false;
          tableHeaders = [];
          tableRows = [];
        }
        continue;
      }

      // Handle horizontal rule
      if (/^---+$/.test(line.trim())) {
        rendered.push(
          <hr
            key={key++}
            className={`my-6 ${isDarkMode ? 'border-slate-600' : 'border-gray-300'}`}
          />
        );
        continue;
      }

      // Handle headings
      const headingMatch = line.match(SAFE_HEADING_PATTERN);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const text = headingMatch[2];
        const HeadingTag = `h${level}`;
        const headingClasses = {
          1: `text-3xl font-bold mt-8 mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`,
          2: `text-2xl font-bold mt-6 mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`,
          3: `text-xl font-semibold mt-5 mb-2 ${isDarkMode ? 'text-slate-100' : 'text-gray-800'}`,
          4: `text-lg font-semibold mt-4 mb-2 ${isDarkMode ? 'text-slate-200' : 'text-gray-700'}`,
          5: `text-base font-medium mt-3 mb-1 ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`,
          6: `text-sm font-medium mt-2 mb-1 ${isDarkMode ? 'text-slate-400' : 'text-gray-500'}`,
        };

        rendered.push(
          React.createElement(
            HeadingTag,
            { key: key++, className: headingClasses[level] },
            parseInlineElements(text, isDarkMode)
          )
        );
        continue;
      }

      // Handle unordered list items
      const listMatch = line.match(SAFE_LIST_PATTERN);
      if (listMatch) {
        const indent = listMatch[1].length;
        const text = listMatch[2];
        rendered.push(
          <li
            key={key++}
            className={`ml-${Math.min(indent / 2 + 4, 12)} list-disc ${
              isDarkMode ? 'text-slate-300' : 'text-gray-600'
            }`}
            style={{ marginLeft: `${indent / 2 + 1.5}rem` }}
          >
            {parseInlineElements(text, isDarkMode)}
          </li>
        );
        continue;
      }

      // Handle ordered list items
      const orderedMatch = line.match(SAFE_ORDERED_LIST_PATTERN);
      if (orderedMatch) {
        const indent = orderedMatch[1].length;
        const text = orderedMatch[2];
        rendered.push(
          <li
            key={key++}
            className={`list-decimal ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}
            style={{ marginLeft: `${indent / 2 + 1.5}rem` }}
          >
            {parseInlineElements(text, isDarkMode)}
          </li>
        );
        continue;
      }

      // Handle empty lines
      if (line.trim() === '') {
        rendered.push(<div key={key++} className="h-4" />);
        continue;
      }

      // Handle regular paragraphs
      rendered.push(
        <p
          key={key++}
          className={`my-2 leading-relaxed ${isDarkMode ? 'text-slate-300' : 'text-gray-600'}`}
        >
          {parseInlineElements(line, isDarkMode)}
        </p>
      );
    }

    return rendered;
  }, [content, isDarkMode, searchQuery]);

  return <div className="prose max-w-none">{elements}</div>;
};

/**
 * Navigation Sidebar Component
 */
const DocNavigation = ({ documents, activeDoc, onSelectDoc, isDarkMode, searchQuery, onSearchChange }) => {
  return (
    <nav
      className={`w-72 h-full flex flex-col border-r ${
        isDarkMode
          ? 'bg-slate-800 border-slate-700'
          : 'bg-white border-gray-200'
      }`}
      aria-label="Documentation navigation"
    >
      {/* Search */}
      <div className={`p-4 border-b ${isDarkMode ? 'border-slate-700' : 'border-gray-200'}`}>
        <div className="relative">
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value.slice(0, MAX_SEARCH_LENGTH))}
            className={`w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none focus:ring-2 ${
              isDarkMode
                ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-400 focus:ring-blue-500'
                : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:ring-blue-500'
            }`}
            aria-label="Search documentation"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-lg" aria-hidden="true">
            🔍
          </span>
        </div>
        {searchQuery && (
          <p className={`mt-2 text-xs ${isDarkMode ? 'text-slate-400' : 'text-gray-500'}`}>
            Searching for: "{searchQuery}"
          </p>
        )}
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4">
        <h2 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
          isDarkMode ? 'text-slate-400' : 'text-gray-500'
        }`}>
          Integration Guides
        </h2>
        <ul className="space-y-1">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                onClick={() => onSelectDoc(doc.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeDoc === doc.id
                    ? isDarkMode
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-100 text-blue-900'
                    : isDarkMode
                      ? 'text-slate-300 hover:bg-slate-700'
                      : 'text-gray-700 hover:bg-gray-100'
                }`}
                aria-current={activeDoc === doc.id ? 'page' : undefined}
              >
                <div className="font-medium text-sm">{doc.title}</div>
                {doc.description && (
                  <div className={`text-xs mt-0.5 ${
                    activeDoc === doc.id
                      ? isDarkMode ? 'text-blue-200' : 'text-blue-700'
                      : isDarkMode ? 'text-slate-400' : 'text-gray-500'
                  }`}>
                    {doc.description}
                  </div>
                )}
                {doc.audience && (
                  <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${
                    doc.audience === 'engineers'
                      ? isDarkMode ? 'bg-purple-900/50 text-purple-300' : 'bg-purple-100 text-purple-700'
                      : isDarkMode ? 'bg-green-900/50 text-green-300' : 'bg-green-100 text-green-700'
                  }`}>
                    {doc.audience === 'engineers' ? 'Technical' : 'Business'}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      <div className={`p-4 border-t ${isDarkMode ? 'border-slate-700' : 'border-gray-200'}`}>
        <div className={`text-xs ${isDarkMode ? 'text-slate-500' : 'text-gray-400'}`}>
          <p>Ascend Platform Documentation</p>
          <p className="mt-1">© OW-kai Technologies Inc.</p>
        </div>
      </div>
    </nav>
  );
};

/**
 * Main Documentation Viewer Component
 */
const DocumentationViewer = ({ getAuthHeaders, user }) => {
  const { isDarkMode } = useTheme();
  const [documents, setDocuments] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [docContent, setDocContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // Load document index
  useEffect(() => {
    const loadDocumentIndex = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetchWithAuth(`${API_BASE_URL}/api/docs/integration`, {
          method: 'GET',
          headers: getAuthHeaders(),
        });

        if (!response.ok) {
          throw new Error(`Failed to load documentation index: ${response.status}`);
        }

        const data = await response.json();
        setDocuments(data.documents || []);

        // Auto-select first document
        if (data.documents && data.documents.length > 0) {
          setActiveDoc(data.documents[0].id);
        }
      } catch (err) {
        console.error('DOC-003: Failed to load documentation index:', err);
        setError('Failed to load documentation. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadDocumentIndex();
  }, [getAuthHeaders]);

  // Load active document content
  useEffect(() => {
    const loadDocContent = async () => {
      if (!activeDoc) return;

      try {
        setLoading(true);
        setError(null);

        const doc = documents.find(d => d.id === activeDoc);
        if (!doc) return;

        const response = await fetchWithAuth(
          `${API_BASE_URL}${doc.path}`,
          {
            method: 'GET',
            headers: getAuthHeaders(),
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to load document: ${response.status}`);
        }

        const content = await response.text();
        setDocContent(content);
      } catch (err) {
        console.error('DOC-003: Failed to load document content:', err);
        setError('Failed to load document content. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadDocContent();
  }, [activeDoc, documents, getAuthHeaders]);

  // Search functionality
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    const query = searchQuery.toLowerCase();
    const results = [];

    // Search in current document content
    if (docContent) {
      const lines = docContent.split('\n');
      lines.forEach((line, index) => {
        if (line.toLowerCase().includes(query)) {
          results.push({
            line: index + 1,
            text: line.substring(0, 100) + (line.length > 100 ? '...' : ''),
            docId: activeDoc,
          });
        }
      });
    }

    setSearchResults(results.slice(0, 20)); // Limit to 20 results
  }, [searchQuery, docContent, activeDoc]);

  const handleSearchChange = useCallback((value) => {
    // Security: Sanitize search input
    const sanitized = value.replace(/[<>'"&]/g, '');
    setSearchQuery(sanitized);
  }, []);

  const handleSelectDoc = useCallback((docId) => {
    setActiveDoc(docId);
    setSearchQuery(''); // Clear search when switching documents
  }, []);

  const activeDocument = documents.find(d => d.id === activeDoc);

  return (
    <div className={`flex h-[calc(100vh-180px)] rounded-xl overflow-hidden shadow-lg ${
      isDarkMode ? 'bg-slate-800' : 'bg-white'
    }`}>
      {/* Navigation Sidebar */}
      <DocNavigation
        documents={documents}
        activeDoc={activeDoc}
        onSelectDoc={handleSelectDoc}
        isDarkMode={isDarkMode}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className={`px-6 py-4 border-b flex items-center justify-between ${
          isDarkMode ? 'border-slate-700 bg-slate-800' : 'border-gray-200 bg-white'
        }`}>
          <div>
            <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              {activeDocument?.title || 'Documentation'}
            </h1>
            {activeDocument?.description && (
              <p className={`text-sm mt-1 ${isDarkMode ? 'text-slate-400' : 'text-gray-500'}`}>
                {activeDocument.description}
              </p>
            )}
          </div>

          {/* Security badge */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
            isDarkMode
              ? 'bg-green-900/30 text-green-400 border border-green-800'
              : 'bg-green-50 text-green-700 border border-green-200'
          }`}>
            <span aria-hidden="true">🔒</span>
            <span>Secure Documentation</span>
          </div>
        </header>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className={`px-6 py-3 border-b ${
            isDarkMode ? 'border-slate-700 bg-slate-750' : 'border-gray-200 bg-gray-50'
          }`}>
            <h2 className={`text-sm font-medium mb-2 ${isDarkMode ? 'text-slate-300' : 'text-gray-700'}`}>
              Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
            </h2>
            <ul className="space-y-1 max-h-32 overflow-y-auto">
              {searchResults.slice(0, 5).map((result, idx) => (
                <li
                  key={idx}
                  className={`text-xs p-2 rounded ${
                    isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-white text-gray-600'
                  }`}
                >
                  <span className={`font-mono ${isDarkMode ? 'text-slate-500' : 'text-gray-400'}`}>
                    Line {result.line}:
                  </span>{' '}
                  {result.text}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Document Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className={`w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4 ${
                  isDarkMode ? 'border-blue-400' : 'border-blue-600'
                }`} />
                <p className={isDarkMode ? 'text-slate-400' : 'text-gray-500'}>
                  Loading documentation...
                </p>
              </div>
            </div>
          ) : error ? (
            <div className={`p-4 rounded-lg border ${
              isDarkMode
                ? 'bg-red-900/20 border-red-800 text-red-300'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}>
              <h3 className="font-semibold mb-1">Error Loading Documentation</h3>
              <p className="text-sm">{error}</p>
              <button
                onClick={() => setActiveDoc(activeDoc)} // Retry
                className={`mt-3 px-4 py-2 text-sm rounded-lg ${
                  isDarkMode
                    ? 'bg-red-800 hover:bg-red-700 text-white'
                    : 'bg-red-100 hover:bg-red-200 text-red-800'
                }`}
              >
                Retry
              </button>
            </div>
          ) : (
            <SecureMarkdownRenderer
              content={docContent}
              isDarkMode={isDarkMode}
              searchQuery={searchQuery}
            />
          )}
        </div>

        {/* Footer */}
        <footer className={`px-6 py-3 border-t text-xs ${
          isDarkMode ? 'border-slate-700 text-slate-500' : 'border-gray-200 text-gray-400'
        }`}>
          <div className="flex items-center justify-between">
            <span>Ascend Enterprise Platform - Integration Documentation</span>
            <span>Version 2.0.0 | © OW-kai Technologies Inc.</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default DocumentationViewer;
