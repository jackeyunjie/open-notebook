"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Send,
  Clock,
  Eye,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  BookOpen,
  MessageCircle,
  Newspaper,
  Instagram,
  Twitter,
  Youtube,
  Plus,
  Trash2,
  Play,
  Pause,
} from "lucide-react";

// Platform configurations
const PLATFORMS = [
  { id: "xiaohongshu", name: "小红书", icon: BookOpen, color: "bg-red-500", maxChars: 1000 },
  { id: "weibo", name: "微博", icon: MessageCircle, color: "bg-yellow-500", maxChars: 5000 },
  { id: "wechat_official", name: "公众号", icon: Newspaper, color: "bg-green-500", maxChars: null },
  { id: "zhihu", name: "知乎", icon: BookOpen, color: "bg-blue-500", maxChars: null },
  { id: "twitter", name: "Twitter/X", icon: Twitter, color: "bg-black", maxChars: 280 },
  { id: "instagram", name: "Instagram", icon: Instagram, color: "bg-purple-500", maxChars: 2200 },
  { id: "youtube", name: "YouTube", icon: Youtube, color: "bg-red-600", maxChars: null },
];

interface PublishJob {
  id: string;
  title: string;
  content_text: string;
  target_platforms: string[];
  status: string;
  scheduled_at?: string;
  published_at?: string;
  platform_urls: Record<string, string>;
}

export default function PublishPage() {
  const [activeTab, setActiveTab] = useState("compose");
  const [jobs, setJobs] = useState<PublishJob[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [content, setContent] = useState({
    title: "",
    text: "",
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [variants, setVariants] = useState<Record<string, any>>({});

  // Mock jobs for demonstration
  useEffect(() => {
    setJobs([
      {
        id: "job_001",
        title: "AI工具推荐：提升10倍效率",
        content_text: "分享5个实用的AI工具...",
        target_platforms: ["xiaohongshu", "weibo"],
        status: "published",
        published_at: "2024-02-14T10:00:00Z",
        platform_urls: {
          xiaohongshu: "https://xiaohongshu.com/...",
          weibo: "https://weibo.com/...",
        },
      },
      {
        id: "job_002",
        title: "内容创作方法论",
        content_text: "从0到10万粉的心路历程...",
        target_platforms: ["zhihu"],
        status: "scheduled",
        scheduled_at: "2024-02-15T09:00:00Z",
        platform_urls: {},
      },
    ]);
  }, []);

  const togglePlatform = (platformId: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platformId)
        ? prev.filter((p) => p !== platformId)
        : [...prev, platformId]
    );
  };

  const addTag = () => {
    if (tagInput && !content.tags.includes(tagInput)) {
      setContent((prev) => ({ ...prev, tags: [...prev.tags, tagInput] }));
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setContent((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== tag) }));
  };

  const handlePreview = () => {
    // Generate platform variants
    const newVariants: Record<string, any> = {};
    selectedPlatforms.forEach((platformId) => {
      const platform = PLATFORMS.find((p) => p.id === platformId);
      if (platform) {
        let text = content.text;
        let title = content.title;

        // Apply platform limits
        if (platform.maxChars && text.length > platform.maxChars) {
          text = text.slice(0, platform.maxChars - 3) + "...";
        }

        // Format hashtags
        const hashtags = content.tags.map((t) => `#${t}#`);

        newVariants[platformId] = {
          title,
          text,
          hashtags,
          platform: platform.name,
        };
      }
    });
    setVariants(newVariants);
    setShowPreview(true);
  };

  const handlePublish = async (schedule?: boolean) => {
    setIsPublishing(true);
    // TODO: Call API to publish
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsPublishing(false);
    setActiveTab("queue");
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "published":
        return <Badge className="bg-green-500">已发布</Badge>;
      case "scheduled":
        return <Badge variant="outline">已定时</Badge>;
      case "publishing":
        return <Badge className="bg-blue-500">发布中</Badge>;
      case "failed":
        return <Badge variant="destructive">失败</Badge>;
      default:
        return <Badge variant="secondary">待发布</Badge>;
    }
  };

  const getCharCount = (platformId: string) => {
    const platform = PLATFORMS.find((p) => p.id === platformId);
    if (!platform?.maxChars) return null;
    return `${content.text.length}/${platform.maxChars}`;
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">内容发布</h1>
        <p className="text-muted-foreground">
          一键分发到多个平台，自动适配格式与限制
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="compose" className="flex items-center gap-2">
            <Send className="w-4 h-4" />
            创作内容
          </TabsTrigger>
          <TabsTrigger value="queue" className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            发布队列
          </TabsTrigger>
          <TabsTrigger value="scheduled" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            定时任务
          </TabsTrigger>
        </TabsList>

        {/* Compose Tab */}
        <TabsContent value="compose" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Content Editor */}
            <Card>
              <CardHeader>
                <CardTitle>内容编辑</CardTitle>
                <CardDescription>
                  编写内容，系统将自动适配各平台格式
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>标题</Label>
                  <Input
                    placeholder="输入内容标题"
                    value={content.title}
                    onChange={(e) =>
                      setContent((prev) => ({ ...prev, title: e.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>正文</Label>
                  <Textarea
                    placeholder="输入内容正文..."
                    rows={10}
                    value={content.text}
                    onChange={(e) =>
                      setContent((prev) => ({ ...prev, text: e.target.value }))
                    }
                  />
                  <p className="text-xs text-muted-foreground text-right">
                    {content.text.length} 字符
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>标签</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="添加标签，按回车确认"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addTag()}
                    />
                    <Button variant="outline" onClick={addTag}>
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {content.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => removeTag(tag)}
                      >
                        #{tag} <XCircle className="w-3 h-3 ml-1" />
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>媒体文件</Label>
                  <div className="border-2 border-dashed rounded-lg p-8 text-center text-muted-foreground">
                    <p>拖拽图片或视频到这里</p>
                    <p className="text-sm">支持 JPG, PNG, MP4, MOV</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Platform Selection */}
            <Card>
              <CardHeader>
                <CardTitle>目标平台</CardTitle>
                <CardDescription>
                  选择要发布的平台，系统将自动适配格式
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {PLATFORMS.map((platform) => {
                    const Icon = platform.icon;
                    const isSelected = selectedPlatforms.includes(platform.id);
                    const charCount = getCharCount(platform.id);

                    return (
                      <div
                        key={platform.id}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                          isSelected
                            ? "border-primary bg-primary/5"
                            : "hover:bg-muted"
                        }`}
                        onClick={() => togglePlatform(platform.id)}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`p-2 rounded-lg ${platform.color} text-white`}
                          >
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-medium">{platform.name}</div>
                            {charCount && (
                              <div
                                className={`text-xs ${
                                  content.text.length >
                                  (platform.maxChars || 9999)
                                    ? "text-red-500"
                                    : "text-muted-foreground"
                                }`}
                              >
                                字数限制: {charCount}
                              </div>
                            )}
                          </div>
                        </div>
                        <Switch checked={isSelected} />
                      </div>
                    );
                  })}
                </div>

                <Separator className="my-4" />

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={handlePreview}
                    disabled={!content.text || selectedPlatforms.length === 0}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    预览效果
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => handlePublish()}
                    disabled={!content.text || selectedPlatforms.length === 0 || isPublishing}
                  >
                    {isPublishing ? (
                      <>
                        <Clock className="w-4 h-4 mr-2 animate-spin" />
                        发布中...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        立即发布
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Queue Tab */}
        <TabsContent value="queue" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>发布队列</CardTitle>
              <CardDescription>查看发布任务状态和历史记录</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {jobs.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>暂无发布任务</p>
                  </div>
                ) : (
                  jobs.map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div>
                        <h3 className="font-medium">{job.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          {job.target_platforms
                            .map(
                              (p) => PLATFORMS.find((platform) => platform.id === p)?.name
                            )
                            .join("、")}
                        </p>
                        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                          {job.published_at && (
                            <span>
                              发布时间: {new Date(job.published_at).toLocaleString("zh-CN")}
                            </span>
                          )}
                          {job.scheduled_at && (
                            <span>
                              定时: {new Date(job.scheduled_at).toLocaleString("zh-CN")}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        {getStatusBadge(job.status)}
                        {job.status === "published" && (
                          <div className="flex gap-2">
                            {Object.entries(job.platform_urls).map(([platform, url]) => (
                              <Button key={platform} variant="ghost" size="sm" asChild>
                                <a href={url} target="_blank" rel="noopener noreferrer">
                                  <CheckCircle className="w-4 h-4" />
                                </a>
                              </Button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scheduled Tab */}
        <TabsContent value="scheduled" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>定时任务</CardTitle>
              <CardDescription>管理定时发布的内容</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {jobs
                  .filter((j) => j.status === "scheduled")
                  .map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div>
                        <h3 className="font-medium">{job.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          计划发布: {new Date(job.scheduled_at || "").toLocaleString("zh-CN")}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Play className="w-4 h-4 mr-2" />
                          立即发布
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                {jobs.filter((j) => j.status === "scheduled").length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>暂无定时任务</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Preview Dialog */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>内容预览</DialogTitle>
            <DialogDescription>
              查看内容在各平台的显示效果
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-4 p-4">
              {Object.entries(variants).map(([platformId, variant]) => {
                const platform = PLATFORMS.find((p) => p.id === platformId);
                if (!platform) return null;
                const Icon = platform.icon;

                return (
                  <Card key={platformId}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`p-1.5 rounded ${platform.color} text-white`}
                        >
                          <Icon className="w-4 h-4" />
                        </div>
                        <span className="font-medium">{platform.name}</span>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-2">
                      {variant.title && (
                        <h4 className="font-semibold mb-2">{variant.title}</h4>
                      )}
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {variant.text}
                      </p>
                      {variant.hashtags?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {variant.hashtags.map((tag: string) => (
                            <span key={tag} className="text-sm text-blue-500">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowPreview(false)}>
              返回编辑
            </Button>
            <Button onClick={() => handlePublish()}>
              <Send className="w-4 h-4 mr-2" />
              确认发布
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
