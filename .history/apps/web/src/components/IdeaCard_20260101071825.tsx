import React from 'react';
import { Idea } from '@/types';
import { LinkIcon, CalendarIcon } from '@heroicons/react/24/outline';

interface IdeaCardProps {
  idea: Idea;
  showCluster?: boolean;
}

export const IdeaCard: React.FC<IdeaCardProps> = ({ idea, showCluster = false }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'danger';
      default:
        return 'slate';
    }
  };

  const sentimentColor = getSentimentColor(idea.sentiment);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.3 }}
      className="card relative group overflow-hidden"
      role="article"
      aria-label={`Idea: ${idea.problem_statement}`}
    >
      {/* Gradient glow on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative z-10">
        {/* Problem Statement */}
        <h3 className="text-lg font-semibold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-purple-400 group-hover:to-pink-400 transition-all duration-300">
          {idea.problem_statement}
        </h3>

        {/* Context (if available) */}
        {idea.context && (
          <p className="text-slate-400 text-sm mb-4 line-clamp-3">
            {idea.context}
          </p>
        )}

        {/* Metadata Row */}
        <div className="flex flex-wrap gap-2 mb-3" role="list" aria-label="Idea metadata">
        {/* Quality Score */}
        <span className="badge" role="listitem" aria-label={`Quality score: ${(idea.quality_score * 100).toFixed(0)} percent`}>
          Quality: {(idea.quality_score * 100).toFixed(0)}%
        </span>

        {/* Sentiment */}
        <span className={`badge-${sentimentColor}`} role="listitem" aria-label={`Sentiment: ${idea.sentiment}`}>
          {idea.sentiment}
        </span>

        {/* Domain (if available) */}
        {idea.domain && (
          <span
            className="badge bg-primary-500/10 text-primary-400 ring-1 ring-inset ring-primary-500/20"
            role="listitem"
            aria-label={`Domain: ${idea.domain}`}
          >
            {idea.domain}
          </span>
        )}
      </div>

      {/* Source Info */}
      <div className="flex items-center gap-4 text-sm text-slate-500 border-t border-slate-700 pt-3">
        {/* Source Link */}
        {idea.source_url && (
          <a
            href={idea.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-primary-400 transition-colors"
            aria-label="View original source in new tab"
          >
            <LinkIcon className="w-4 h-4" aria-hidden="true" />
            <span>View Source</span>
          </a>
        )}

        {/* Date */}
        {idea.extracted_at && (
          <div className="flex items-center gap-1" aria-label={`Extracted on ${new Date(idea.extracted_at).toLocaleDateString()}`}>
            <CalendarIcon className="w-4 h-4" aria-hidden="true" />
            <span>{new Date(idea.extracted_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {/* Cluster Badge (if applicable) */}
      {showCluster && idea.cluster && (
        <div className="mt-3 pt-3 border-t border-slate-700">
          <span className="text-xs text-slate-500">Part of cluster:</span>
          <span className="ml-2 text-sm text-primary-400 font-medium">
            {idea.cluster.label}
          </span>
        </div>
      )}
    </div>
  );
};
