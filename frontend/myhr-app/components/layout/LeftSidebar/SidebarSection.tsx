"use client"

import { useRouter } from "next/navigation"
import { ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { MenuItem } from "./types"

interface SidebarSectionProps {
  item: MenuItem
  expandedSections: string[]
  activeId: string
  onToggle: (sectionId: string) => void
  onSetActive: (id: string) => void
  level: number
}

export default function SidebarSection({ item, expandedSections, activeId, onToggle, onSetActive, level }: SidebarSectionProps) {
  const router = useRouter()
  const Icon = item.icon
  const isExpanded = expandedSections.includes(item.id)

  const handleClick = () => {
    if (item.children) {
      onToggle(item.id)
    } else if (item.path) {
      onSetActive(item.id)
      router.push(item.path)
    }
  }

  const handleChildClick = (child: MenuItem) => {
    if (child.path) {
      onSetActive(child.id)
      router.push(child.path)
    } else if (child.children) {
      onToggle(child.id)
    }
  }

  return (
    <div className="mb-1">
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start py-3 h-auto text-left",
          "text-[var(--sidebar-fg)] hover:bg-[#5277F1] transition-colors",
          activeId === item.id && "bg-[var(--primary)]/30 border-l-4 border-[var(--primary)] text-white font-medium",
        )}
        onClick={handleClick}
      >
        <Icon className="h-5 w-5 mr-3" />
        <span className="flex-1">{item.label}</span>
        {item.children && <ChevronRight className={cn("h-4 w-4 transition-transform", isExpanded && "rotate-90")} />}
      </Button>

      {item.children && isExpanded && (
        <div className="mt-1 space-y-1" style={{ marginLeft: level === 0 ? 32 : 24 }}>
          {item.children.map((child) => (
            child.children ? (
              <SidebarSection
                key={child.id}
                item={child}
                expandedSections={expandedSections}
                activeId={activeId}
                onToggle={onToggle}
                onSetActive={onSetActive}
                level={level + 1}
              />
            ) : (
              <Button
                key={child.id}
                variant="ghost"
                className={cn(
                  "w-full justify-start px-4 py-2 h-auto text-left text-sm",
                  "text-[var(--sidebar-fg)]/90 hover:bg-[#5277F1] transition-colors",
                  activeId === child.id &&
                    "bg-[var(--primary)]/25 border-l-3 border-[var(--primary)] text-white font-medium",
                )}
                onClick={() => handleChildClick(child)}
              >
                {child.label}
              </Button>
            )
          ))}
        </div>
      )}
    </div>
  )
}
