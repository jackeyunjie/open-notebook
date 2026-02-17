/**
 * OPC Activity Monitor - Background Service Worker
 *
 * Tracks user activity patterns for IP self-understanding.
 * Privacy-first: All data stored locally in browser storage.
 */

// Activity tracking state
let currentActivity = {
  url: null,
  title: null,
  domain: null,
  startTime: null,
  category: 'other'
};

// Category mapping for common domains
const categoryMap = {
  // Content creation
  'figma.com': 'design',
  'canva.com': 'design',
  'youtube.com': 'content-consumption',
  'bilibili.com': 'content-consumption',
  'xiaohongshu.com': 'content-consumption',
  'douyin.com': 'content-consumption',

  // Knowledge work
  'notion.so': 'knowledge-management',
  'roamresearch.com': 'knowledge-management',
  'obsidian.md': 'knowledge-management',
  'logseq.com': 'knowledge-management',

  // Writing
  'docs.google.com': 'writing',
  'yuque.com': 'writing',
  'zhihu.com': 'writing',
  'medium.com': 'writing',
  'substack.com': 'writing',

  // Research
  'scholar.google.com': 'research',
  'arxiv.org': 'research',
  'github.com': 'coding',
  'stackoverflow.com': 'coding',

  // Social/Marketing
  'twitter.com': 'social-media',
  'x.com': 'social-media',
  'weibo.com': 'social-media',
  'linkedin.com': 'networking',

  // Communication
  'gmail.com': 'communication',
  'outlook.com': 'communication',
  'feishu.cn': 'communication',
  'dingtalk.com': 'communication',

  // Shopping/Distraction (for pattern recognition)
  'taobao.com': 'shopping',
  'jd.com': 'shopping',
  'amazon.com': 'shopping'
};

// Initialize
chrome.runtime.onStartup.addListener(initializeTracker);
chrome.runtime.onInstalled.addListener(initializeTracker);

async function initializeTracker() {
  console.log('[OPC Monitor] Initialized');

  // Set up periodic sync to local API
  chrome.alarms.create('sync-to-opc', { periodInMinutes: 1 });

  // Clean old data (keep 7 days locally)
  await cleanupOldData();
}

// Listen for tab activation
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  await recordCurrentActivity();
  await startNewActivity(activeInfo.tabId);
});

// Listen for tab updates (URL changes)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.active) {
    await recordCurrentActivity();
    await startNewActivity(tabId);
  }
});

// Listen for window focus changes
chrome.windows.onFocusChanged.addListener(async (windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    // Window lost focus - pause tracking
    await recordCurrentActivity();
  } else {
    // Window gained focus - resume tracking
    const [tab] = await chrome.tabs.query({ active: true, windowId });
    if (tab) {
      await startNewActivity(tab.id);
    }
  }
});

// Start tracking new activity
async function startNewActivity(tabId) {
  try {
    const tab = await chrome.tabs.get(tabId);

    if (!tab.url || tab.url.startsWith('chrome://')) {
      return;
    }

    const url = new URL(tab.url);
    const domain = url.hostname.replace('www.', '');

    currentActivity = {
      url: tab.url,
      title: tab.title,
      domain: domain,
      startTime: Date.now(),
      category: categorizeDomain(domain)
    };

  } catch (error) {
    console.error('[OPC Monitor] Error starting activity:', error);
  }
}

// Record completed activity
async function recordCurrentActivity() {
  if (!currentActivity.startTime) return;

  const duration = Date.now() - currentActivity.startTime;

  // Only record if activity lasted more than 5 seconds
  if (duration < 5000) return;

  const activityRecord = {
    ...currentActivity,
    duration: duration,
    endTime: Date.now(),
    date: new Date().toISOString().split('T')[0]
  };

  // Store locally
  await storeActivity(activityRecord);

  // Reset current activity
  currentActivity = {
    url: null,
    title: null,
    domain: null,
    startTime: null,
    category: 'other'
  };
}

// Categorize domain
function categorizeDomain(domain) {
  for (const [pattern, category] of Object.entries(categoryMap)) {
    if (domain.includes(pattern)) {
      return category;
    }
  }
  return 'other';
}

// Store activity in local storage
async function storeActivity(activity) {
  const key = `activities_${activity.date}`;

  const result = await chrome.storage.local.get([key]);
  const activities = result[key] || [];

  activities.push(activity);

  await chrome.storage.local.set({ [key]: activities });

  console.log('[OPC Monitor] Activity recorded:', activity.domain, activity.duration);
}

// Sync to local OPC API
async function syncToOPC() {
  try {
    const today = new Date().toISOString().split('T')[0];
    const key = `activities_${today}`;

    const result = await chrome.storage.local.get([key]);
    const activities = result[key] || [];

    if (activities.length === 0) return;

    // Calculate daily summary
    const summary = calculateDailySummary(activities);

    // Send to local OPC API
    const response = await fetch('http://localhost:5055/api/v1/activity/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        date: today,
        activities: activities.slice(-50), // Last 50 activities
        summary: summary,
        timestamp: Date.now()
      })
    });

    if (response.ok) {
      console.log('[OPC Monitor] Synced to OPC');
    }
  } catch (error) {
    // Silent fail - will retry next minute
    console.log('[OPC Monitor] Sync failed (OPC may not be running):', error.message);
  }
}

// Calculate daily activity summary
function calculateDailySummary(activities) {
  const categoryTime = {};
  const domainTime = {};
  let totalTime = 0;

  activities.forEach(activity => {
    // By category
    categoryTime[activity.category] = (categoryTime[activity.category] || 0) + activity.duration;

    // By domain
    domainTime[activity.domain] = (domainTime[activity.domain] || 0) + activity.duration;

    totalTime += activity.duration;
  });

  return {
    totalTime,
    categoryTime,
    domainTime: Object.entries(domainTime)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10), // Top 10 domains
    activityCount: activities.length
  };
}

// Cleanup old data (keep 7 days)
async function cleanupOldData() {
  const allKeys = await chrome.storage.local.get(null);
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 7);
  const cutoffStr = cutoffDate.toISOString().split('T')[0];

  const keysToDelete = Object.keys(allKeys).filter(key => {
    if (!key.startsWith('activities_')) return false;
    const dateStr = key.replace('activities_', '');
    return dateStr < cutoffStr;
  });

  if (keysToDelete.length > 0) {
    await chrome.storage.local.remove(keysToDelete);
    console.log('[OPC Monitor] Cleaned up old data:', keysToDelete.length, 'days');
  }
}

// Alarm handler for periodic sync
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sync-to-opc') {
    syncToOPC();
  }
});

// Message handler for popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getTodayActivities') {
    getTodayActivities().then(sendResponse);
    return true; // Async response
  }

  if (request.action === 'getCurrentActivity') {
    const now = Date.now();
    sendResponse({
      ...currentActivity,
      currentDuration: currentActivity.startTime ? (now - currentActivity.startTime) : 0
    });
  }
});

async function getTodayActivities() {
  const today = new Date().toISOString().split('T')[0];
  const key = `activities_${today}`;
  const result = await chrome.storage.local.get([key]);
  return result[key] || [];
}