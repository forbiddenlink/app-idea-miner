import React from 'react';
import { motion } from 'framer-motion';
import { Idea } from '@/types';
import { ExternalLink, Calendar, Link as LinkIcon } from 'lucide-react';
import { ContextMenu, createIdeaContextMenu } from './ContextMenu';

interface IdeaCardProps {
  idea: Idea;
  showCluster?: boolean;
}

export const IdeaCard: React.FC<IdeaCardProps> = ({ idea, showCluster = false }) => {
  const contextMenuItems = createIdeaContextMenu({
    id: idea.id,
    problem_statement: idea.problem_statement,
    source: idea.source_url ? { url: idea.source_url } : undefined,
  });

  const sentimentColor = idea.sentiment.toLowerCase() === 'positive'
    ? 'text-success'
    : idea.sentiment.toLowerCase() === 'negative'
      ? 'text-destructive'
      : 'text-muted-foreground';

  return (
    <ContextMenu items={contextMenuItems}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="group rounded-lg border border-border bg-card p-5 transition-colors hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        role="article"
        aria-label={`Idea: ${idea.problem_statement}`}
      >
        {/* Problem Statement */}
        <h3 className="mb-2 text-base font-semibold leading-snug text-foreground transition-colors group-hover:text-primary">
          {idea.problem_statement}
        </h3>

        {/* Context */}
        {idea.context && (
          <p className="mb-4 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {idea.context}
          </p>
        )}

        {/* Metadata Row */}
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          {/* Quality Score */}
          <span title="Quality Score">
            {(idea.quality_score * 100).toFixed(0)}% quality
          </span>

          <span className="text-border">·</span>

          {/* Sentiment */}
          <span className={sentimentColor}>
            {idea.sentiment}
          </span>

          {/* Domain */}
          {idea.domain && (
            <>
              <span className="text-border">·</span>
              <span>{idea.domain}</span>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            {/* Date */}
            {idea.extracted_at && (
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                <span>{new Date(idea.extracted_at).toLocaleDateString()}</span>
              </div>
            )}

            {/* Cluster Info */}
            {showCluster && idea.cluster && (
              <div className="hidden items-center gap-1.5 sm:flex">
                <LinkIcon className="h-3.5 w-3.5" />
                <span className="line-clamp-1 max-w-[150px] font-medium text-primary">
                  {idea.cluster.label}
                </span>
              </div>
            )}
          </div>

          {/* Source Link */}
          {idea.source_url && (
            <a
              href={idea.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 transition-colors hover:text-foreground"
              aria-label="View original source"
            >
              <span>Source</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </motion.div>
    </ContextMenu>
  );
};
