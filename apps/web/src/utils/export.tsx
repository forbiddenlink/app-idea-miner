// Data Export Utilities
// Export cluster data, analytics, and trend reports as CSV/JSON

export interface ExportData {
  filename: string;
  data: unknown;
  format: 'csv' | 'json';
}

/**
 * Download data as JSON file
 */
export const exportAsJSON = (data: unknown, filename: string) => {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  downloadBlob(blob, `${filename}.json`);
};

/**
 * Download data as CSV file
 */
export const exportAsCSV = (data: Record<string, unknown>[], filename: string) => {
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

import { Cluster, Idea, DomainStats, TrendDataPoint } from '@/types';

/**
 * Export cluster evidence as CSV
 */
export const exportClusterEvidence = (cluster: Cluster, evidence: Idea[], format: 'csv' | 'json' = 'csv') => {
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
      'Extracted Date': idea.extracted_at ? new Date(idea.extracted_at).toLocaleDateString() : 'N/A',
    }));
    exportAsCSV(csvData, filename);
  }
};

/**
 * Export analytics domain breakdown as CSV
 */
export const exportDomainBreakdown = (domains: DomainStats[], format: 'csv' | 'json' = 'csv') => {
  const filename = `domain-breakdown-${new Date().toISOString().split('T')[0]}`;

  if (format === 'json') {
    exportAsJSON(domains, filename);
  } else {
    const csvData = domains.map(d => ({
      'Domain': d.domain,
      'Idea Count': d.idea_count,
      'Percentage': `${d.percentage}%`,
    }));
    exportAsCSV(csvData, filename);
  }
};

/**
 * Export trend data as CSV
 */
export const exportTrendData = (trends: TrendDataPoint[], metric: string, format: 'csv' | 'json' = 'csv') => {
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
