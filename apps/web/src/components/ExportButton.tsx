import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { Cluster, Idea } from '@/types';
import { apiClient } from '@/services/api';
import { useGlobalToast } from '@/contexts/ToastContext';

type ExportFormat = 'csv' | 'json';
type ExportType = 'clusters' | 'ideas' | 'analytics';

interface ExportButtonProps {
  type: ExportType;
  data?: unknown;
  className?: string;
}

export const ExportButton = ({ type, data, className = '' }: ExportButtonProps) => {
  const toast = useGlobalToast();
  const [isExporting, setIsExporting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const menuId = `export-menu-${type}`;

  useEffect(() => {
    if (!showMenu) return;
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowMenu(false);
      }
    };
    document.addEventListener('keydown', onEscape);
    return () => document.removeEventListener('keydown', onEscape);
  }, [showMenu]);

  const toCsvCell = (value: unknown): string => {
    const stringValue = value == null ? '' : String(value);
    return `"${stringValue.replaceAll('"', '""')}"`;
  };

  const fetchAllClusters = async (): Promise<Cluster[]> => {
    const allClusters: Cluster[] = []
    let offset = 0
    const limit = 100

    while (true) {
      const response = await apiClient.getClusters({ limit, offset })
      allClusters.push(...response.clusters)
      if (!response.pagination?.has_more) break
      offset += limit
    }

    return allClusters
  }

  const fetchAllIdeas = async (): Promise<Idea[]> => {
    const allIdeas: Idea[] = []
    let offset = 0
    const limit = 100

    while (true) {
      const response = await apiClient.getIdeas({ limit, offset })
      allIdeas.push(...response.ideas)
      if (!response.pagination?.has_more) break
      offset += limit
    }

    return allIdeas
  }

  const exportToCSV = (data: Record<string, unknown>[], filename: string) => {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.map(toCsvCell).join(','),
      ...data.map((row) =>
        headers.map((header) => {
          const value = row[header];
          if (Array.isArray(value)) {
            return toCsvCell(value.map(String).join('; '));
          }
          if (typeof value === 'object' && value !== null) {
            return toCsvCell(JSON.stringify(value));
          }
          return toCsvCell(value);
        }).join(',')
      ),
    ].join('\n');

    downloadFile(csvContent, filename, 'text/csv');
  };



  const exportToJSON = (data: unknown, filename: string) => {
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
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setShowMenu(false);

    try {
      let exportData: unknown;
      let filename: string;

      if (data) {
        // Use provided data
        exportData = data;
        filename = `app-idea-miner-${type}-${new Date().toISOString().split('T')[0]}.${format}`;
      } else {
        // Fetch data from API
        switch (type) {
          case 'clusters': {
            const clusters = await fetchAllClusters()
            exportData = clusters.map((c: Cluster) => ({
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
            const ideas = await fetchAllIdeas()
            exportData = ideas.map((i: Idea) => ({
              id: i.id,
              problem_statement: i.problem_statement,
              sentiment: i.sentiment,
              sentiment_score: i.sentiment_score,
              quality_score: i.quality_score,
              domain: i.domain,
              cluster_label: i.cluster?.label || 'Unclustered',
              source_url: i.source_url || i.raw_post?.url,
              extracted_at: i.extracted_at,
            }));
            filename = `ideas-${new Date().toISOString().split('T')[0]}.${format}`;
            break;
          }

          case 'analytics': {
            exportData = await apiClient.getAnalyticsSummary()
            filename = `analytics-${new Date().toISOString().split('T')[0]}.${format}`;
            break;
          }

          default:
            throw new Error('Invalid export type');
        }
      }

      if (format === 'csv') {
        if (Array.isArray(exportData)) {
          exportToCSV(exportData as Record<string, unknown>[], filename);
        } else {
          // Convert object to array for CSV
          const flattenedData = [exportData as Record<string, unknown>];
          exportToCSV(flattenedData, filename);
        }
      } else {
        exportToJSON(exportData, filename);
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export data. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setShowMenu(!showMenu)}
        disabled={isExporting}
        className={`focus-ring flex h-10 items-center gap-2 rounded-xl border border-border bg-card px-4 text-sm font-semibold text-foreground shadow-raised transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
        aria-label={`Export ${type} data`}
        aria-haspopup="true"
        aria-controls={menuId}
        aria-expanded={showMenu}
      >
        <Download className="w-5 h-5" aria-hidden="true" />
        <span>{isExporting ? 'Exporting…' : 'Export'}</span>
      </button>

      {showMenu && !isExporting && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
            aria-hidden="true"
          />

          {/* Menu */}
          <div
            id={menuId}
            className="absolute right-0 z-20 mt-2 w-48 rounded-xl border border-border bg-popover shadow-overlay"
            aria-label="Export format options"
          >
            <button
              type="button"
              onClick={() => handleExport('csv')}
              className="focus-ring w-full rounded-t-xl px-4 py-2 text-left text-sm font-medium text-popover-foreground transition-colors hover:bg-accent"
              aria-label="Export as CSV file"
            >
              Export as CSV
            </button>
            <button
              type="button"
              onClick={() => handleExport('json')}
              className="focus-ring w-full rounded-b-xl px-4 py-2 text-left text-sm font-medium text-popover-foreground transition-colors hover:bg-accent"
              aria-label="Export as JSON file"
            >
              Export as JSON
            </button>
          </div>
        </>
      )}
    </div>
  );
};
