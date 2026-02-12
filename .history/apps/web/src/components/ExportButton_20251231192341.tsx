import { useState } from 'react';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

type ExportFormat = 'csv' | 'json';
type ExportType = 'clusters' | 'ideas' | 'analytics';

interface ExportButtonProps {
  type: ExportType;
  data?: any;
  className?: string;
}

export const ExportButton = ({ type, data, className = '' }: ExportButtonProps) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const exportToCSV = (data: any[], filename: string) => {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map((row) =>
        headers.map((header) => {
          const value = row[header];
          // Handle arrays and objects
          if (Array.isArray(value)) {
            return `"${value.join('; ')}"`;
          }
          if (typeof value === 'object' && value !== null) {
            return `"${JSON.stringify(value)}"`;
          }
          // Escape quotes in strings
          if (typeof value === 'string' && value.includes(',')) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value || '';
        }).join(',')
      ),
    ].join('\n');

    downloadFile(csvContent, filename, 'text/csv');
  };

  const exportToJSON = (data: any, filename: string) => {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, filename, 'application/json');
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setShowMenu(false);

    try {
      let exportData: any;
      let filename: string;

      if (data) {
        // Use provided data
        exportData = data;
        filename = `app-idea-miner-${type}-${new Date().toISOString().split('T')[0]}.${format}`;
      } else {
        // Fetch data from API
        switch (type) {
          case 'clusters': {
            const response = await axios.get('http://localhost:8000/api/v1/clusters?limit=1000');
            exportData = response.data.clusters.map((c: any) => ({
              id: c.id,
              label: c.label,
              idea_count: c.idea_count,
              avg_sentiment: c.avg_sentiment,
              quality_score: c.quality_score,
              trend_score: c.trend_score,
              keywords: c.keywords.join('; '),
              created_at: c.created_at,
            }));
            filename = `clusters-${new Date().toISOString().split('T')[0]}.${format}`;
            break;
          }

          case 'ideas': {
            const response = await axios.get('http://localhost:8000/api/v1/ideas?limit=1000');
            exportData = response.data.ideas.map((i: any) => ({
              id: i.id,
              problem_statement: i.problem_statement,
              sentiment: i.sentiment,
              sentiment_score: i.sentiment_score,
              quality_score: i.quality_score,
              domain: i.domain,
              cluster_label: i.cluster?.label || 'Unclustered',
              source_url: i.source?.url,
              extracted_at: i.extracted_at,
            }));
            filename = `ideas-${new Date().toISOString().split('T')[0]}.${format}`;
            break;
          }

          case 'analytics': {
            const response = await axios.get('http://localhost:8000/api/v1/analytics/summary');
            exportData = response.data;
            filename = `analytics-${new Date().toISOString().split('T')[0]}.${format}`;
            break;
          }

          default:
            throw new Error('Invalid export type');
        }
      }

      if (format === 'csv') {
        if (Array.isArray(exportData)) {
          exportToCSV(exportData, filename);
        } else {
          // Convert object to array for CSV
          const flattenedData = [exportData];
          exportToCSV(flattenedData, filename);
        }
      } else {
        exportToJSON(exportData, filename);
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export data. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={isExporting}
        className={`flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
        aria-label="Export data"
        aria-haspopup="true"
        aria-expanded={showMenu}
      >
        <ArrowDownTrayIcon className="w-5 h-5" />
        <span>{isExporting ? 'Exporting...' : 'Export'}</span>
      </button>

      {showMenu && !isExporting && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />

          {/* Menu */}
          <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20">
            <button
              onClick={() => handleExport('csv')}
              className="w-full text-left px-4 py-2 hover:bg-slate-700 text-slate-200 transition-colors rounded-t-lg"
            >
              Export as CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              className="w-full text-left px-4 py-2 hover:bg-slate-700 text-slate-200 transition-colors rounded-b-lg"
            >
              Export as JSON
            </button>
          </div>
        </>
      )}
    </div>
  );
};
