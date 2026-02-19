import { motion, HTMLMotionProps } from "framer-motion"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/utils/cn"

interface StatCardProps extends Omit<HTMLMotionProps<"div">, "children"> {
  name: string
  value: string
  change?: string
  trend?: "up" | "down" | "neutral"
  trendValue?: string
}

export default function StatCard({
  name,
  value,
  change,
  trend,
  trendValue,
  className,
  ...props
}: StatCardProps) {
  const getTrendIcon = () => {
    if (!trend) return null

    const iconClass = "h-3.5 w-3.5"
    switch (trend) {
      case "up":
        return <TrendingUp className={cn(iconClass, "text-success")} />
      case "down":
        return <TrendingDown className={cn(iconClass, "text-destructive")} />
      default:
        return <Minus className={cn(iconClass, "text-muted-foreground")} />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-success"
      case "down":
        return "text-destructive"
      default:
        return "text-muted-foreground"
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "rounded-lg border border-border bg-card p-6 transition-colors",
        className
      )}
      {...props}
    >
      <div className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">{name}</p>
        <p className="text-3xl font-semibold tracking-tight">{value}</p>

        {(change || trendValue) && (
          <div className="flex items-center gap-1.5 text-xs">
            {trend && trendValue && (
              <span className={cn("flex items-center gap-1", getTrendColor())}>
                {getTrendIcon()}
                {trendValue}
              </span>
            )}
            {change && (
              <span className="text-muted-foreground">
                {trendValue && "·"} {change}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
