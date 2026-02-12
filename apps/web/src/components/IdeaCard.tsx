
import React from 'react';
import { motion } from 'framer-motion';
import { Idea } from '@/types';
import { ExternalLink, Calendar, Link as LinkIcon, Sparkles } from 'lucide-react';
import { ContextMenu, createIdeaContextMenu } from './ContextMenu';
import { cn } from '@/utils/cn';
import { cva } from "class-variance-authority";

interface IdeaCardProps {
  idea: Idea;
  showCluster?: boolean;
}

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success: "border-transparent bg-green-500/15 text-green-600 dark:text-green-500 hover:bg-green-500/25",
        danger: "border-transparent bg-red-500/15 text-red-600 dark:text-red-500 hover:bg-red-500/25",
        primary: "border-transparent bg-blue-500/15 text-blue-600 dark:text-blue-500 hover:bg-blue-500/25",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export const IdeaCard: React.FC<IdeaCardProps> = ({ idea, showCluster = false }) => {
  // Context menu items
  const contextMenuItems = createIdeaContextMenu({
    id: idea.id,
    problem_statement: idea.problem_statement,
    source: idea.source_url ? { url: idea.source_url } : undefined,
  })

  // Map sentiment to badge variant
  const getSentimentVariant = (sentiment: string): "success" | "danger" | "secondary" | "primary" => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  const sentimentVariant = getSentimentVariant(idea.sentiment);

  return (
    <ContextMenu items={contextMenuItems}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -4 }}
        transition={{ duration: 0.3 }}
        className="group relative overflow-hidden rounded-xl border bg-card text-card-foreground shadow transition-all hover:shadow-md hover:border-primary/50"
        role="article"
        aria-label={`Idea: ${idea.problem_statement}`}
      >
        <div className="p-6">
          {/* Problem Statement */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold leading-relaxed tracking-tight group-hover:text-primary transition-colors">
              {idea.problem_statement}
            </h3>
          </div>

          {/* Context (if available) */}
          {idea.context && (
            <p className="mb-6 text-sm text-muted-foreground line-clamp-3 leading-relaxed">
              {idea.context}
            </p>
          )}

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            {/* Quality Score */}
            <span
              className={cn(badgeVariants({ variant: "outline" }), "bg-muted/50")}
              title="Quality Score"
            >
              <Sparkles className="mr-1 h-3 w-3 text-yellow-500" />
              {(idea.quality_score * 100).toFixed(0)}%
            </span>

            {/* Sentiment */}
            <span className={cn(badgeVariants({ variant: sentimentVariant }))}>
              {idea.sentiment}
            </span>

            {/* Domain */}
            {idea.domain && (
              <span className={cn(badgeVariants({ variant: "secondary" }))}>
                {idea.domain}
              </span>
            )}
          </div>

          {/* Footer Info */}
          <div className="flex items-center justify-between border-t pt-4 text-xs text-muted-foreground">
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
                <div className="flex items-center gap-1.5 hidden sm:flex">
                  <LinkIcon className="h-3.5 w-3.5" />
                  <span className="font-medium text-primary line-clamp-1 max-w-[150px]">
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
                className="flex items-center gap-1.5 hover:text-primary transition-colors"
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
