// Loading skeleton components for better UX while data fetches

export const StatCardSkeleton = () => (
  <div className="card animate-pulse">
    <div className="flex items-center justify-between">
      <div className="space-y-3 flex-1">
        <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-24"></div>
        <div className="h-8 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded backdrop-blur-sm w-16"></div>
      </div>
      <div className="h-12 w-12 bg-gradient-to-br from-indigo-600/20 to-purple-600/20 rounded-lg backdrop-blur-sm"></div>
    </div>
    <div className="mt-4 h-3 bg-gradient-to-r from-slate-700/20 to-slate-600/20 rounded backdrop-blur-sm w-32"></div>
  </div>
);

export const ClusterCardSkeleton = () => (
  <div className="card animate-pulse">
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="h-6 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded backdrop-blur-sm w-3/4"></div>
          <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-1/2"></div>
        </div>
        <div className="h-8 w-8 bg-gradient-to-br from-indigo-600/20 to-purple-600/20 rounded backdrop-blur-sm"></div>
      </div>

      {/* Keywords */}
      <div className="flex flex-wrap gap-2">
        <div className="h-6 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 rounded-full backdrop-blur-sm w-20"></div>
        <div className="h-6 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-full backdrop-blur-sm w-24"></div>
        <div className="h-6 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 rounded-full backdrop-blur-sm w-16"></div>
        <div className="h-6 bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-full backdrop-blur-sm w-28"></div>
      </div>

      {/* Metrics */}
      <div className="flex gap-4 pt-4 border-t border-slate-700/30">
        <div className="space-y-1">
          <div className="h-3 bg-gradient-to-r from-slate-700/20 to-slate-600/20 rounded backdrop-blur-sm w-12"></div>
          <div className="h-5 bg-gradient-to-r from-slate-700/40 to-slate-600/40 rounded backdrop-blur-sm w-8"></div>
        </div>
        <div className="space-y-1">
          <div className="h-3 bg-gradient-to-r from-slate-700/20 to-slate-600/20 rounded backdrop-blur-sm w-16"></div>
          <div className="h-5 bg-gradient-to-r from-slate-700/40 to-slate-600/40 rounded backdrop-blur-sm w-12"></div>
        </div>
        <div className="space-y-1">
          <div className="h-3 bg-gradient-to-r from-slate-700/20 to-slate-600/20 rounded backdrop-blur-sm w-12"></div>
          <div className="h-5 bg-gradient-to-r from-slate-700/40 to-slate-600/40 rounded backdrop-blur-sm w-10"></div>
        </div>
      </div>
    </div>
  </div>
);

export const IdeaCardSkeleton = () => (
  <div className="card animate-pulse">
    <div className="space-y-3">
      <div className="h-5 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded backdrop-blur-sm w-full"></div>
      <div className="h-5 bg-gradient-to-r from-slate-700/40 to-slate-600/40 rounded backdrop-blur-sm w-5/6"></div>
      <div className="flex items-center gap-2 pt-2">
        <div className="h-6 bg-gradient-to-r from-green-600/20 to-emerald-600/20 rounded-full backdrop-blur-sm w-20"></div>
        <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-32"></div>
      </div>
    </div>
  </div>
);

export const ChartSkeleton = () => (
  <div className="card animate-pulse">
    <div className="space-y-4">
      <div className="h-6 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded backdrop-blur-sm w-48"></div>
      <div className="h-64 bg-gradient-to-br from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm"></div>
    </div>
  </div>
);

export const TableSkeleton = () => (
  <div className="card overflow-hidden animate-pulse">
    <div className="p-6 space-y-4">
      <div className="h-6 bg-gradient-to-r from-slate-700/50 to-slate-600/50 rounded backdrop-blur-sm w-32"></div>
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-24"></div>
            <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-16"></div>
            <div className="h-4 bg-gradient-to-r from-slate-700/30 to-slate-600/30 rounded backdrop-blur-sm w-20"></div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export const DetailHeaderSkeleton = () => (
  <div className="space-y-6 animate-pulse">
    {/* Title and metrics */}
    <div className="space-y-4">
      <div className="h-8 bg-slate-700 rounded w-2/3"></div>
      <div className="h-5 bg-slate-700 rounded w-full"></div>
    </div>

    {/* Metric cards */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-slate-800 rounded-lg p-4">
          <div className="h-4 bg-slate-700 rounded w-16 mb-2"></div>
          <div className="h-6 bg-slate-700 rounded w-12"></div>
        </div>
      ))}
    </div>

    {/* Keywords */}
    <div className="space-y-3">
      <div className="h-5 bg-slate-700 rounded w-24"></div>
      <div className="flex flex-wrap gap-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-7 bg-slate-700 rounded-full w-20"></div>
        ))}
      </div>
    </div>
  </div>
);
