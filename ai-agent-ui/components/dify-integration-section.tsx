"use client"

import { useState, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Workflow, Database, MessageSquare } from "lucide-react"
import Image from "next/image"

// 비디오 팝업 카드 컴포넌트
function VideoPopupCard({
  icon: Icon,
  iconBg,
  iconColor,
  title,
  description,
  videoSrc,
}: {
  icon: React.ElementType
  iconBg: string
  iconColor: string
  title: string
  description: string
  videoSrc?: string
}) {
  const [isHovered, setIsHovered] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const handleMouseEnter = () => {
    setIsHovered(true)
    if (videoRef.current) {
      videoRef.current.currentTime = 0
      videoRef.current.play()
    }
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    if (videoRef.current) {
      videoRef.current.pause()
    }
  }

  return (
    <div 
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <Card className="border-border/50 bg-card p-6 transition-all hover:shadow-lg cursor-pointer">
        <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${iconBg} ${iconColor}`}>
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="mb-2 font-semibold">{title}</h3>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      </Card>
      
      {/* 비디오 팝업 */}
      {videoSrc && isHovered && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 z-50 animate-in fade-in zoom-in-95 duration-200">
          <div className="rounded-xl overflow-hidden shadow-2xl border border-border/50 bg-card">
            <video
              ref={videoRef}
              src={videoSrc}
              className="w-80 h-auto"
              muted
              loop
              playsInline
            />
          </div>
          {/* 화살표 */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1">
            <div className="w-3 h-3 bg-card border-r border-b border-border/50 transform rotate-45" />
          </div>
        </div>
      )}
    </div>
  )
}

export function DifyIntegrationSection() {
  return (
    <section id="integration" className="border-y border-border/40 bg-secondary/30 py-32">
      <div className="container mx-auto px-6">
        <div className="mb-12 flex items-center justify-center gap-3">
          <span className="text-4xl font-bold tracking-tight text-foreground">M-axis</span>
          <span className="text-3xl font-light text-muted-foreground">+</span>
          <Image 
            src="/dify.png" 
            alt="Dify" 
            width={80} 
            height={32} 
            className="h-8 w-auto object-contain" 
          />
        </div>

        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">
            Seamlessly Connected to M-axis & Dify
          </h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            Built on SK AX's M-axis manufacturing platform with Dify's powerful AI orchestration, providing a unified
            experience for building and deploying intelligent production agents.
          </p>
        </div>

        <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-3">
          <VideoPopupCard
            icon={Workflow}
            iconBg="from-emerald-500/20 to-teal-500/20"
            iconColor="text-emerald-600 dark:text-emerald-400"
            title="Workflow Engine"
            description="Leverage Dify's visual workflow builder for custom error handling logic"
            videoSrc="/dify_workflow.mp4"
          />

          <VideoPopupCard
            icon={Database}
            iconBg="from-blue-500/20 to-cyan-500/20"
            iconColor="text-blue-600 dark:text-blue-400"
            title="Knowledge Base"
            description="Connect to Dify's knowledge management for context-aware responses"
          />

          <VideoPopupCard
            icon={MessageSquare}
            iconBg="from-purple-500/20 to-pink-500/20"
            iconColor="text-purple-600 dark:text-purple-400"
            title="LLM Models"
            description="Access multiple AI models through Dify's unified API gateway"
          />
        </div>
      </div>
    </section>
  )
}
