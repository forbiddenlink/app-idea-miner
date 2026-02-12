// Data Export Utilities
// Export cluster data, analytics, and trend reports as CSV/JSON

export interface ExportData {
  filename: string;
  data: any;
  format: 'csv' | 'json';
}

/**
 * Download data as JSON file
 */
export const exportAsJSON = (data: any, filename: string) => {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  downloadBlob(blob, `${filename}.json`);
};

/**
 * Download data as CSV file
 */
export const exportAsCSV = (data: any[], filename: string) => {
  if (data.length === 0) {
    console.warn('No data to export');
    return;
  }

  // Get headers from first object
  const headers = Object.keys(data[0]);

  // Convert to CSV format
  const csvRows = [
    headers.join(','), // Header row
    ...data.map(row =>
      headers.map(header => {
        const value = row[header];
        // Handle quotes and commas in values
        const stringValue = String(value ?? '');
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    )
  ];

  const csvString = csvRows.join('\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  downloadBlob(blob, `${filename}.csv`);
};

/**
 * Helper to trigger browser download
 */
const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export cluster evidence as CSV
 */
export const exportClusterEvidence = (cluster: any, evidence: any[], format: 'csv' | 'json' = 'csv') => {
  const filename = `cluster-${cluster.label.replace(/\s+/g, '-').toLowerCase()}-evidence`;

  if (format === 'json') {
    exportAsJSON({ cluster, evidence }, filename);
  } else {
    const csvData = evidence.map(idea => ({
      'Problem Statement': idea.problem_statement,
      'Sentiment': idea.sentiment,
      'Sentiment Score': idea.sentiment_score.toFixed(2),
      'Quality Score': idea.quality_score.toFixed(2),
      'Domain': idea.domain || 'N/A',
      'Source URL': idea.source_url || 'N/A',
      'Published Date': idea.published_at ? new Date(idea.published_at).toLocaleDateString() : 'N/A',
    }));
    exportAsCSV(csvData, filename);
  }
};

/**
 * Export analytics domain breakdown as CSV
 */
export const exportDomainBreakdown = (domains: any[], format: 'csv' | 'json' = 'csv') => {
  const filename = `domain-breakdown-${new Date().toISOString().split('T')[0]}`;

  if (format === 'json') {
    exportAsJSON(domains, filename);
  } else {
    const csvData = domains.map(d => ({
      'Domain': d.domain,
      'Idea Count': d.count,
      'Percentage': `${d.percentage}%`,
    }));
    exportAsCSV(csvData, filename);
  }
};

/**
 * Export trend data as CSV
 */
export const exportTrendData = (trends: any[], metric: string, format: 'csv' | 'json' = 'csv') => {
  const filename = `trends-${metric}-${new Date().toISOString().split('T')[0]}`;

  if (format === 'json') {
    exportAsJSON(trends, filename);
  } else {
    const csvData = trends.map(t => ({
      'Date': t.date,
      'Value': t.value,
      'Average Sentiment': t.avg_sentiment ? t.avg_sentiment.toFixed(2) : 'N/A',
    }));
    exportAsCSV(csvData, filename);
  }
};

// Export button component
interface ExportButtonProps {
  onExport: (format: 'csv' | 'json') => void;
  label?: string;
  disabled?: boolean;
}

export const ExportButton = ({ onExport, label = 'Export', disabled = false }: ExportButtonProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-md
                   transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center gap-2"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        {label}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-32 bg-slate-800 border border-slate-700 rounded-md shadow-lg z-10">
          <button
            onClick={() => {
              onExport('csv');
              setIsOpen(false);
            }}
            className="w-full px-4 py-2 text-left text-slate-200 hover:bg-slate-700 rounded-t-md"
          >
            Export CSV
          </button>
          <button
            onClick={() => {
              onExport('json');
              setIsOpen(false);
            }}
            className="w-full px-4 py-2 text-left text-slate-200 hover:bg-slate-700 rounded-b-md"
          >
            Export JSON
          </button>
        </div>
      )}
    </div>
  );
};

// Missing import
import { useState } from 'react';
