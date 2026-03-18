import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Idea } from '@/types';
import { ExternalLink, Calendar, Link as LinkIcon, Heart } from 'lucide-react';
import { useFavorites } from '@/hooks/useFavorites';
import { ContextMenu, createIdeaContextMenu } from './ContextMenu';
import { cn } from '@/utils/cn';

interface IdeaCardProps {
  idea: Idea;
  showCluster?: boolean;
}

export const IdeaCard: React.FC<IdeaCardProps> = ({ idea, showCluster = false }) => {
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorited = isFavorite(idea.id, 'idea')
  const contextMenuItems = createIdeaContextMenu({
    id: idea.id,
    problem_statement: idea.problem_statement,
    source: idea.source_url ? { url: idea.source_url } : undefined,
  }, () => toggleFavorite(idea.id, 'idea'), favorited);

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
        className="group card card-hover p-5"
        role="article"
        aria-label={`Idea: ${idea.problem_statement}`}
      >
        <div className="mb-2 flex items-start justify-between gap-3">
          {/* Problem Statement */}
          <h3 className="text-base font-semibold leading-snug text-foreground transition-colors group-hover:text-primary">
            <Link to={`/ideas/${idea.id}`} className="hover:underline underline-offset-2">
              {idea.problem_statement}
            </Link>
          </h3>

          <button
            type="button"
            onClick={() => toggleFavorite(idea.id, 'idea')}
            aria-pressed={favorited}
            aria-label={favorited ? 'Remove idea from favorites' : 'Add idea to favorites'}
            className={cn(
              "focus-ring shrink-0 rounded-lg p-1.5 transition-colors hover:bg-accent",
              favorited ? "text-red-500" : "text-muted-foreground hover:text-red-400"
            )}
          >
            <Heart className={cn("h-4 w-4", favorited && "fill-current")} />
          </button>
        </div>

        {/* Context */}
        {idea.context && (
          <p className="mb-4 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {idea.context}
          </p>
        )}

        {/* Metadata Row */}
        <div className="mb-4 flex flex-wrap items-center gap-2 border-b border-border/70 pb-4 text-sm text-muted-foreground">
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
        <div className="flex items-center justify-between pt-4 text-xs text-muted-foreground">
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
          <div className="flex items-center gap-3">
            <Link
              to={`/ideas/${idea.id}`}
              className="flex items-center gap-1.5 transition-colors hover:text-foreground"
              aria-label="View idea details"
            >
              <span>Details</span>
              <LinkIcon className="h-3.5 w-3.5" />
            </Link>
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
        </div>
      </motion.div>
    </ContextMenu>
  );
};
