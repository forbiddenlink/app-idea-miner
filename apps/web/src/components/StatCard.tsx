import { cva, type VariantProps } from "class-variance-authority"
import { motion, HTMLMotionProps } from "framer-motion"
import { LucideIcon } from "lucide-react"
import { cn } from "@/utils/cn"

const statCardVariants = cva(
  "card relative overflow-hidden p-6 transition-all hover:shadow-md",
  {
    variants: {
      themeColor: {
        primary: "border-l-4 border-l-primary",
        success: "border-l-4 border-l-green-500",
        warning: "border-l-4 border-l-yellow-500",
        danger: "border-l-4 border-l-destructive",
      },
    },
    defaultVariants: {
      themeColor: "primary",
    },
  }
)

const iconVariants = cva("rounded-xl p-3", {
  variants: {
    themeColor: {
      primary: "bg-primary/10 text-primary",
      success: "bg-green-500/10 text-green-500",
      warning: "bg-yellow-500/10 text-yellow-500",
      danger: "bg-destructive/10 text-destructive",
    },
  },
  defaultVariants: {
    themeColor: "primary",
  },
})

// Omit 'color' from HTML props to avoid conflict if we used color (though we changed to themeColor)
// Also use HTMLMotionProps for direct motion compatibility
interface StatCardProps
  extends Omit<HTMLMotionProps<"div">, "color">,
  VariantProps<typeof statCardVariants> {
  name: string
  value: string
  icon: LucideIcon
  change?: string
  // Map legacy logical color prop to our internal themeColor variant
  color?: "primary" | "success" | "warning" | "danger"
}

export default function StatCard({
  name,
  value,
  icon: Icon,
  color = "primary",
  className,
  change,
  ...props
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className={cn(statCardVariants({ themeColor: color }), className)}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{name}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {change && (
            <p className="text-xs text-muted-foreground">{change}</p>
          )}
        </div>
        <div className={cn(iconVariants({ themeColor: color }))}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </motion.div>
  )
}
