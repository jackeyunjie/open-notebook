"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  UserCircle,
  Calendar,
  BarChart3,
  Target,
  Lightbulb,
  Network,
  Settings,
  TrendingUp,
  BookOpen,
  Brain,
  Bot,
  History,
} from "lucide-react";

// Types for 10-dimensional profile
interface DimensionHealth {
  [key: string]: number;
}

interface ProfileSummary {
  profile_id: string;
  name: string;
  version: number;
  dimensions: {
    d1_static_identity: {
      core_values_count: number;
      positioning: string;
    };
    d2_dynamic_behavior: {
      content_frequency: string;
      platforms: string[];
    };
    d3_value_drivers: {
      expertise_areas: string[];
      content_pillars: string[];
    };
    d4_relationship_network: {
      audience_segments: number;
      key_relationships: number;
    };
    d7_knowledge_assets: {
      published_count: number;
      top_content: number;
    };
    d10_cognitive_evolution: {
      evolution_logs_count: number;
      pivot_points: number;
    };
  };
  last_updated: string;
}

// Dimension definitions
const DIMENSIONS = [
  { id: "d1", name: "静态身份", icon: UserCircle, color: "bg-blue-500" },
  { id: "d2", name: "动态行为", icon: TrendingUp, color: "bg-green-500" },
  { id: "d3", name: "价值驱动", icon: Target, color: "bg-purple-500" },
  { id: "d4", name: "关系网络", icon: Network, color: "bg-orange-500" },
  { id: "d5", name: "环境约束", icon: Settings, color: "bg-gray-500" },
  { id: "d6", name: "动态反馈", icon: BarChart3, color: "bg-red-500" },
  { id: "d7", name: "知识资产", icon: BookOpen, color: "bg-indigo-500" },
  { id: "d8", name: "默会知识", icon: Brain, color: "bg-pink-500" },
  { id: "d9", name: "AI协作", icon: Bot, color: "bg-cyan-500" },
  { id: "d10", name: "认知进化", icon: History, color: "bg-teal-500" },
];

export default function IPCommandCenter() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [profile, setProfile] = useState<ProfileSummary | null>(null);
  const [dimensionHealth, setDimensionHealth] = useState<DimensionHealth>({});
  const [overallCompleteness, setOverallCompleteness] = useState(0);

  // TODO: Replace with actual API calls
  useEffect(() => {
    // Mock data for now
    setProfile({
      profile_id: "profile_001",
      name: "我的IP档案",
      version: 1,
      dimensions: {
        d1_static_identity: {
          core_values_count: 3,
          positioning: "AI赋能的内容创作者...",
        },
        d2_dynamic_behavior: {
          content_frequency: "每周3-4篇",
          platforms: ["小红书", "公众号", "即刻"],
        },
        d3_value_drivers: {
          expertise_areas: ["AI工具", "内容创作", "个人成长"],
          content_pillars: ["AI实战", "创作方法论"],
        },
        d4_relationship_network: {
          audience_segments: 4,
          key_relationships: 12,
        },
        d7_knowledge_assets: {
          published_count: 47,
          top_content: 5,
        },
        d10_cognitive_evolution: {
          evolution_logs_count: 8,
          pivot_points: 2,
        },
      },
      last_updated: "2024-02-14T10:30:00Z",
    });

    setDimensionHealth({
      d1_static_identity: 0.6,
      d2_dynamic_behavior: 0.8,
      d3_value_drivers: 0.75,
      d4_relationship_network: 0.4,
      d5_environmental_constraints: 0.3,
      d6_dynamic_feedback: 0.5,
      d7_knowledge_assets: 0.7,
      d8_tacit_knowledge: 0.2,
      d9_ai_collaboration: 0.6,
      d10_cognitive_evolution: 0.45,
    });

    setOverallCompleteness(0.55);
  }, []);

  const getHealthColor = (score: number) => {
    if (score >= 0.8) return "bg-green-500";
    if (score >= 0.5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getHealthStatus = (score: number) => {
    if (score >= 0.8) return "完整";
    if (score >= 0.5) return "进行中";
    return "待完善";
  };

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">个人IP指挥中心</h1>
        <p className="text-muted-foreground">
          10维档案 · 内容日历 · 数据看板 · 一体化管理
        </p>
      </div>

      {/* Overall Progress */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            档案完整度
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Progress value={overallCompleteness * 100} className="h-3" />
            </div>
            <span className="text-lg font-semibold">
              {Math.round(overallCompleteness * 100)}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {overallCompleteness >= 0.8
              ? "档案已相当完整，继续保持！"
              : overallCompleteness >= 0.5
              ? "档案正在完善中，继续补充各维度信息"
              : "档案需要大量完善，建议从核心维度开始"}
          </p>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            数据看板
          </TabsTrigger>
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <UserCircle className="w-4 h-4" />
            10维档案
          </TabsTrigger>
          <TabsTrigger value="calendar" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            内容日历
          </TabsTrigger>
          <TabsTrigger value="platforms" className="flex items-center gap-2">
            <Network className="w-4 h-4" />
            平台管理
          </TabsTrigger>
          <TabsTrigger value="p0-p3" className="flex items-center gap-2">
            <Bot className="w-4 h-4" />
            有机体系统
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">47</div>
                <p className="text-sm text-muted-foreground">已发布内容</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">12</div>
                <p className="text-sm text-muted-foreground">进行中</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">28</div>
                <p className="text-sm text-muted-foreground">选题储备</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">156</div>
                <p className="text-sm text-muted-foreground">总互动数</p>
              </CardContent>
            </Card>
          </div>

          {/* Quadrant Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>四象限内容分布</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-blue-700">Q1 意向用户</span>
                    <Badge variant="secondary">15篇</Badge>
                  </div>
                  <p className="text-sm text-blue-600">你有问题，我有方案</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-green-700">Q2 认知用户</span>
                    <Badge variant="secondary">12篇</Badge>
                  </div>
                  <p className="text-sm text-green-600">你知道这个领域，我帮你深化</p>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-purple-700">Q3 泛用户</span>
                    <Badge variant="secondary">18篇</Badge>
                  </div>
                  <p className="text-sm text-purple-600">广泛传播，建立认知</p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-orange-700">Q4 潜在用户</span>
                    <Badge variant="secondary">8篇</Badge>
                  </div>
                  <p className="text-sm text-orange-600">发现新场景，创造需求</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 10-Dimension Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {DIMENSIONS.map((dim) => {
              const health = dimensionHealth[dim.id + "_" + dim.name.toLowerCase().replace(/\s/g, "_")] || 0;
              const Icon = dim.icon;

              return (
                <Card key={dim.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className={`p-2 rounded-lg ${dim.color} bg-opacity-10`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <Badge
                        variant={health >= 0.8 ? "default" : "secondary"}
                        className={health >= 0.8 ? "bg-green-500" : ""}
                      >
                        {getHealthStatus(health)}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg mt-3">
                      {dim.id.toUpperCase()}. {dim.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">完整度</span>
                        <span>{Math.round(health * 100)}%</span>
                      </div>
                      <Progress value={health * 100} className="h-2" />
                    </div>
                    <Button variant="outline" className="w-full mt-4" size="sm">
                      编辑维度
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Calendar Tab */}
        <TabsContent value="calendar" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>内容日历</CardTitle>
              <Button>
                <Lightbulb className="w-4 h-4 mr-2" />
                新建选题
              </Button>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-muted-foreground">
                <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>日历功能开发中...</p>
                <p className="text-sm">将集成P0-P3系统自动生成选题</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Platforms Tab */}
        <TabsContent value="platforms" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>已连接平台</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  连接自媒体平台，自动同步内容数据到P0感知层
                </p>
              </div>
              <Link href="/ip-center/platforms">
                <Button>管理平台账号</Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { name: "小红书", status: "已连接", count: 47, color: "bg-red-500" },
                  { name: "微博", status: "已连接", count: 128, color: "bg-yellow-500" },
                  { name: "公众号", status: "未连接", count: 0, color: "bg-gray-300" },
                  { name: "知乎", status: "未连接", count: 0, color: "bg-gray-300" },
                ].map((platform) => (
                  <div
                    key={platform.name}
                    className={`p-4 rounded-lg border ${platform.status === "已连接" ? "border-primary" : ""}`}
                  >
                    <div className={`w-3 h-3 rounded-full ${platform.color} mb-2`} />
                    <div className="font-medium">{platform.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {platform.status === "已连接"
                        ? `${platform.count} 条内容`
                        : "点击连接"}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* P0-P3 System Tab */}
        <TabsContent value="p0-p3" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>有机体系统状态</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="font-semibold">P0 感知层</span>
                  </div>
                  <p className="text-sm text-muted-foreground">4个Agent运行中</p>
                  <p className="text-xs text-muted-foreground mt-1">今日扫描: 23个信号</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="font-semibold">P1 价值层</span>
                  </div>
                  <p className="text-sm text-muted-foreground">4个Agent运行中</p>
                  <p className="text-xs text-muted-foreground mt-1">待评估: 8个信号</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="font-semibold">P2 关系层</span>
                  </div>
                  <p className="text-sm text-muted-foreground">4个Agent运行中</p>
                  <p className="text-xs text-muted-foreground mt-1">执行中: 3个计划</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse" />
                    <span className="font-semibold">P3 进化层</span>
                  </div>
                  <p className="text-sm text-muted-foreground">第12代策略</p>
                  <p className="text-xs text-muted-foreground mt-1">适配图: +15%</p>
                </div>
              </div>

              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">最近进化报告</h4>
                <p className="text-sm text-muted-foreground">
                  第12代进化完成。Q1象限策略改进显著，点击率提升23%。
                  建议增加早8点发布频率。
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
