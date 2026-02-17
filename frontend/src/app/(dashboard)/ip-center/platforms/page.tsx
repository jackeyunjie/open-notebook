"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  RefreshCw,
  Plus,
  Unlink,
  CheckCircle,
  XCircle,
  AlertCircle,
  ExternalLink,
  Database,
  TrendingUp,
  FileText,
  Instagram,
  Twitter,
  Youtube,
  MessageCircle,
  BookOpen,
  Video,
  Newspaper,
} from "lucide-react";

// Platform configurations
const PLATFORM_CONFIGS: Record<string, {
  name: string;
  icon: React.ReactNode;
  color: string;
  authType: string;
  description: string;
}> = {
  xiaohongshu: {
    name: "小红书",
    icon: <BookOpen className="w-5 h-5" />,
    color: "bg-red-500",
    authType: "Cookie",
    description: "生活方式分享平台，适合图文笔记和短视频",
  },
  weibo: {
    name: "微博",
    icon: <MessageCircle className="w-5 h-5" />,
    color: "bg-yellow-500",
    authType: "Cookie",
    description: "社交媒体平台，适合热点话题和快速传播",
  },
  wechat_official: {
    name: "公众号",
    icon: <Newspaper className="w-5 h-5" />,
    color: "bg-green-500",
    authType: "API Key",
    description: "微信内容平台，适合深度长文和私域运营",
  },
  zhihu: {
    name: "知乎",
    icon: <BookOpen className="w-5 h-5" />,
    color: "bg-blue-500",
    authType: "Cookie",
    description: "问答社区，适合专业知识和深度内容",
  },
  bilibili: {
    name: "B站",
    icon: <Video className="w-5 h-5" />,
    color: "bg-pink-500",
    authType: "Cookie",
    description: "视频社区，适合中长视频和二次元内容",
  },
  twitter: {
    name: "X / Twitter",
    icon: <Twitter className="w-5 h-5" />,
    color: "bg-black",
    authType: "OAuth2",
    description: "全球社交媒体，适合短文本和国际化内容",
  },
  instagram: {
    name: "Instagram",
    icon: <Instagram className="w-5 h-5" />,
    color: "bg-purple-500",
    authType: "OAuth2",
    description: "图片分享平台，适合视觉内容和生活方式",
  },
  youtube: {
    name: "YouTube",
    icon: <Youtube className="w-5 h-5" />,
    color: "bg-red-600",
    authType: "OAuth2",
    description: "视频平台，适合长视频和全球观众",
  },
};

interface ConnectedAccount {
  id: string;
  platform: string;
  username: string;
  display_name: string;
  is_authenticated: boolean;
  auto_sync: boolean;
  last_sync_at: string | null;
  last_sync_status: string;
  total_content_fetched: number;
}

interface PlatformContent {
  id: string;
  platform_content_id: string;
  title: string;
  content_type: string;
  platform_created_at: string;
  engagement: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
    saves: number;
  };
  platform_url: string;
  quadrant: string | null;
}

export default function PlatformManagement() {
  const [activeTab, setActiveTab] = useState("accounts");
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<ConnectedAccount | null>(null);
  const [contents, setContents] = useState<PlatformContent[]>([]);
  const [isConnectDialogOpen, setIsConnectDialogOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [cookieInput, setCookieInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState<Record<string, boolean>>({});

  // Mock data for demonstration
  useEffect(() => {
    setAccounts([
      {
        id: "acc_001",
        platform: "xiaohongshu",
        username: "vikki_ai",
        display_name: "Vikki的AI笔记",
        is_authenticated: true,
        auto_sync: true,
        last_sync_at: "2024-02-14T10:30:00Z",
        last_sync_status: "success",
        total_content_fetched: 47,
      },
      {
        id: "acc_002",
        platform: "weibo",
        username: "vikki_creator",
        display_name: "Vikki创作者",
        is_authenticated: true,
        auto_sync: true,
        last_sync_at: "2024-02-14T09:00:00Z",
        last_sync_status: "success",
        total_content_fetched: 128,
      },
    ]);
  }, []);

  const handleConnect = async () => {
    if (!selectedPlatform || !cookieInput) return;

    setIsLoading(true);
    // TODO: Call API to connect account
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setIsConnectDialogOpen(false);
    setCookieInput("");
    setSelectedPlatform(null);
  };

  const handleSync = async (accountId: string) => {
    setIsSyncing((prev) => ({ ...prev, [accountId]: true }));
    // TODO: Call API to sync account
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsSyncing((prev) => ({ ...prev, [accountId]: false }));
  };

  const handleDisconnect = async (accountId: string) => {
    // TODO: Call API to disconnect account
    setAccounts((prev) => prev.filter((a) => a.id !== accountId));
  };

  const loadAccountContent = async (account: ConnectedAccount) => {
    setSelectedAccount(account);
    // TODO: Call API to load content
    // Mock content
    setContents([
      {
        id: "content_001",
        platform_content_id: "123456",
        title: "AI工具推荐：提升10倍效率的5个神器",
        content_type: "note",
        platform_created_at: "2024-02-13T08:00:00Z",
        engagement: {
          views: 5234,
          likes: 342,
          comments: 56,
          shares: 89,
          saves: 201,
        },
        platform_url: "https://xiaohongshu.com/...",
        quadrant: "Q1",
      },
      {
        id: "content_002",
        platform_content_id: "123457",
        title: "内容创作方法论：从0到10万粉",
        content_type: "note",
        platform_created_at: "2024-02-10T10:00:00Z",
        engagement: {
          views: 8932,
          likes: 567,
          comments: 123,
          shares: 234,
          saves: 445,
        },
        platform_url: "https://xiaohongshu.com/...",
        quadrant: "Q2",
      },
    ]);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return <Badge className="bg-green-500">正常</Badge>;
      case "failed":
        return <Badge variant="destructive">失败</Badge>;
      case "running":
        return <Badge variant="outline">同步中...</Badge>;
      default:
        return <Badge variant="secondary">待同步</Badge>;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + "w";
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + "k";
    }
    return num.toString();
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">平台账号管理</h1>
        <p className="text-muted-foreground">
          连接自媒体平台，同步内容数据，驱动P0-P3有机体系统
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="accounts">已连接账号</TabsTrigger>
          <TabsTrigger value="add">添加新平台</TabsTrigger>
          <TabsTrigger value="content" disabled={!selectedAccount}>
            内容预览
          </TabsTrigger>
        </TabsList>

        <TabsContent value="accounts" className="space-y-6">
          {accounts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Database className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-4">暂无连接的账号</p>
                <Button onClick={() => setActiveTab("add")}>
                  <Plus className="w-4 h-4 mr-2" />
                  添加平台账号
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {accounts.map((account) => {
                const config = PLATFORM_CONFIGS[account.platform];
                return (
                  <Card key={account.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className={`p-3 rounded-lg ${config.color} text-white`}>
                            {config.icon}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold">{config.name}</h3>
                              {account.is_authenticated ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-500" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              @{account.username}
                            </p>
                            <div className="flex items-center gap-4 mt-2 text-sm">
                              <span className="text-muted-foreground">
                                已同步 {account.total_content_fetched} 条内容
                              </span>
                              <span className="text-muted-foreground">
                                上次同步: {account.last_sync_at
                                  ? new Date(account.last_sync_at).toLocaleString("zh-CN")
                                  : "从未"}
                              </span>
                              {getStatusBadge(account.last_sync_status)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSync(account.id)}
                            disabled={isSyncing[account.id]}
                          >
                            <RefreshCw className={`w-4 h-4 mr-2 ${isSyncing[account.id] ? "animate-spin" : ""}`} />
                            同步
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => loadAccountContent(account)}
                          >
                            <FileText className="w-4 h-4 mr-2" />
                            查看内容
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() => handleDisconnect(account.id)}
                          >
                            <Unlink className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="add" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(PLATFORM_CONFIGS).map(([key, config]) => {
              const isConnected = accounts.some((a) => a.platform === key);
              return (
                <Card
                  key={key}
                  className={`cursor-pointer transition-all ${
                    isConnected ? "opacity-50" : "hover:shadow-md hover:border-primary"
                  }`}
                  onClick={() => {
                    if (!isConnected) {
                      setSelectedPlatform(key);
                      setIsConnectDialogOpen(true);
                    }
                  }}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className={`p-2 rounded-lg ${config.color} text-white`}>
                        {config.icon}
                      </div>
                      {isConnected && (
                        <Badge variant="secondary">已连接</Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg">{config.name}</CardTitle>
                    <CardDescription>{config.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span className="font-medium">认证方式:</span>
                      <Badge variant="outline">{config.authType}</Badge>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          {selectedAccount && (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">
                    {PLATFORM_CONFIGS[selectedAccount.platform].name} 内容
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    @{selectedAccount.username} · {contents.length} 条内容
                  </p>
                </div>
                <Button onClick={() => handleSync(selectedAccount.id)}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新数据
                </Button>
              </div>

              <div className="grid gap-4">
                {contents.map((content) => (
                  <Card key={content.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-medium mb-1">{content.title}</h3>
                          <p className="text-sm text-muted-foreground mb-2">
                            {new Date(content.platform_created_at).toLocaleString("zh-CN")}
                          </p>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="flex items-center gap-1">
                              <TrendingUp className="w-4 h-4" />
                              {formatNumber(content.engagement.views)} 浏览
                            </span>
                            <span className="flex items-center gap-1">
                              ❤️ {formatNumber(content.engagement.likes)}
                            </span>
                            <span className="flex items-center gap-1">
                              💬 {formatNumber(content.engagement.comments)}
                            </span>
                            <span className="flex items-center gap-1">
                              📤 {formatNumber(content.engagement.shares)}
                            </span>
                            {content.engagement.saves > 0 && (
                              <span className="flex items-center gap-1">
                                🔖 {formatNumber(content.engagement.saves)}
                              </span>
                            )}
                            {content.quadrant && (
                              <Badge variant="outline">{content.quadrant}</Badge>
                            )}
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" asChild>
                          <a href={content.platform_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={isConnectDialogOpen} onOpenChange={setIsConnectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              连接 {selectedPlatform && PLATFORM_CONFIGS[selectedPlatform].name}
            </DialogTitle>
            <DialogDescription>
              请输入Cookie或认证信息来连接你的账号
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Cookie / 认证信息</Label>
              <Textarea
                placeholder="请粘贴从浏览器开发者工具复制的Cookie..."
                value={cookieInput}
                onChange={(e) => setCookieInput(e.target.value)}
                rows={5}
              />
              <p className="text-xs text-muted-foreground">
                Cookie仅存储在本地，用于同步你的内容数据
              </p>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsConnectDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleConnect} disabled={!cookieInput || isLoading}>
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  连接中...
                </>
              ) : (
                "连接账号"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
