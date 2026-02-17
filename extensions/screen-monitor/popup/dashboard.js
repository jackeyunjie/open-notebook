/**
 * OPC Activity Monitor - Dashboard Logic
 */

// Category colors for visualization
const categoryColors = {
  'design': '#f3e5f5',
  'content-consumption': '#ffebee',
  'knowledge-management': '#e3f2fd',
  'writing': '#e8f5e9',
  'coding': '#fff3e0',
  'research': '#f3e5f5',
  'social-media': '#fce4ec',
  'communication': '#e0f2f1',
  'shopping': '#fbe9e7',
  'other': '#f5f5f5'
};

const categoryNames = {
  'design': '设计创作',
  'content-consumption': '内容消费',
  'knowledge-management': '知识管理',
  'writing': '写作',
  'coding': '编程',
  'research': '研究',
  'social-media': '社交媒体',
  'communication': '沟通协作',
  'shopping': '购物',
  'other': '其他'
};

const categoryIcons = {
  'design': '🎨',
  'content-consumption': '📺',
  'knowledge-management': '📚',
  'writing': '✍️',
  'coding': '💻',
  'research': '🔍',
  'social-media': '💬',
  'communication': '📧',
  'shopping': '🛒',
  'other': '📄'
};

// Format duration
function formatDuration(ms) {
  const minutes = Math.floor(ms / 60000);
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours > 0) {
    return `${hours}h ${remainingMinutes}m`;
  }
  return `${minutes}m`;
}

// Update current activity display
async function updateCurrentActivity() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getCurrentActivity' });

    const container = document.getElementById('current-activity');

    if (!response.url) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">😴</div>
          <div class="empty-state-text">当前无活动</div>
        </div>
      `;
      return;
    }

    const icon = categoryIcons[response.category] || '📄';
    const duration = formatDuration(response.currentDuration);

    container.innerHTML = `
      <div class="current-activity">
        <div class="activity-icon ${response.category}">${icon}</div>
        <div class="activity-info">
          <div class="activity-domain">${response.domain || 'Unknown'}</div>
          <div class="activity-duration">已停留 ${duration}</div>
        </div>
      </div>
    `;
  } catch (error) {
    console.error('Error updating current activity:', error);
  }
}

// Update today's stats
async function updateTodayStats() {
  try {
    const activities = await chrome.runtime.sendMessage({ action: 'getTodayActivities' });

    if (!activities || activities.length === 0) {
      document.getElementById('total-time').textContent = '0h';
      document.getElementById('activity-count').textContent = '0';
      document.getElementById('focus-time').textContent = '0h';
      document.getElementById('switch-count').textContent = '0';
      return;
    }

    // Calculate stats
    const totalTime = activities.reduce((sum, a) => sum + a.duration, 0);
    const activityCount = activities.length;

    // Focus time: activities longer than 10 minutes
    const focusActivities = activities.filter(a => a.duration > 600000);
    const focusTime = focusActivities.reduce((sum, a) => sum + a.duration, 0);

    // Count domain switches
    let switchCount = 0;
    for (let i = 1; i < activities.length; i++) {
      if (activities[i].domain !== activities[i-1].domain) {
        switchCount++;
      }
    }

    document.getElementById('total-time').textContent = formatDuration(totalTime);
    document.getElementById('activity-count').textContent = activityCount;
    document.getElementById('focus-time').textContent = formatDuration(focusTime);
    document.getElementById('switch-count').textContent = switchCount;

    // Update category breakdown
    updateCategoryBreakdown(activities);

    // Update top sites
    updateTopSites(activities);

    // Generate insights
    generateInsights(activities, totalTime, focusTime, switchCount);

  } catch (error) {
    console.error('Error updating stats:', error);
  }
}

// Update category breakdown
function updateCategoryBreakdown(activities) {
  const categoryTime = {};
  let totalTime = 0;

  activities.forEach(a => {
    const cat = a.category || 'other';
    categoryTime[cat] = (categoryTime[cat] || 0) + a.duration;
    totalTime += a.duration;
  });

  // Sort by time
  const sortedCategories = Object.entries(categoryTime)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5); // Top 5

  const container = document.getElementById('category-breakdown');

  if (sortedCategories.length === 0) {
    container.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">暂无数据</div>';
    return;
  }

  container.innerHTML = sortedCategories.map(([category, time]) => {
    const percentage = totalTime > 0 ? (time / totalTime * 100) : 0;
    const color = categoryColors[category] || categoryColors.other;

    return `
      <div class="category-item">
        <span class="category-name">${categoryNames[category] || category}</span>
        <div class="category-bar-bg">
          <div class="category-bar-fill" style="width: ${percentage}%; background: ${color};"></div>
        </div>
        <span class="category-time">${formatDuration(time)}</span>
      </div>
    `;
  }).join('');
}

// Update top sites
function updateTopSites(activities) {
  const domainTime = {};

  activities.forEach(a => {
    domainTime[a.domain] = (domainTime[a.domain] || 0) + a.duration;
  });

  const sortedDomains = Object.entries(domainTime)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const container = document.getElementById('top-sites');

  if (sortedDomains.length === 0) {
    container.innerHTML = '<div style="text-align: center; color: #999;">暂无数据</div>';
    return;
  }

  container.innerHTML = sortedDomains.map(([domain, time]) => `
    <div class="site-item">
      <span class="site-domain">${domain}</span>
      <span class="site-time">${formatDuration(time)}</span>
    </div>
  `).join('');
}

// Generate AI insights
function generateInsights(activities, totalTime, focusTime, switchCount) {
  const insights = [];

  // Insight 1: Focus ratio
  const focusRatio = totalTime > 0 ? (focusTime / totalTime) : 0;
  if (focusRatio > 0.6) {
    insights.push({
      title: '深度工作状态',
      text: '你今天有超过60%的时间处于专注状态，这是高质量产出的保证。'
    });
  } else if (focusRatio < 0.3) {
    insights.push({
      title: '注意力分散',
      text: '专注时间占比偏低，建议尝试番茄工作法，减少上下文切换。'
    });
  }

  // Insight 2: Switch frequency
  const avgSessionTime = activities.length > 0 ? (totalTime / activities.length) : 0;
  if (avgSessionTime < 120000) { // Less than 2 minutes per session
    insights.push({
      title: '频繁切换',
      text: '平均每个页面停留不到2分钟，可能存在多任务焦虑。建议一次只做一件事。'
    });
  } else if (avgSessionTime > 600000) { // More than 10 minutes
    insights.push({
      title: '良好的沉浸度',
      text: '平均每个任务专注10分钟以上，这种深度工作模式效率很高。'
    });
  }

  // Insight 3: Category balance
  const categories = new Set(activities.map(a => a.category));
  if (categories.size > 4) {
    insights.push({
      title: '多元探索',
      text: '你今天涉足了多个领域，这种跨领域学习有助于创新思维。'
    });
  } else if (categories.size < 2 && totalTime > 3600000) {
    insights.push({
      title: '单一专注',
      text: '今天你主要聚焦在一个领域，这种单点突破适合攻坚难题。'
    });
  }

  // Default insight if none generated
  if (insights.length === 0) {
    insights.push({
      title: '持续记录中',
      text: '继续浏览和工作，我会分析你的行为模式并提供个性化建议。'
    });
  }

  const container = document.getElementById('insights');
  container.innerHTML = insights.map(i => `
    <div class="insight-item">
      <div class="insight-title">${i.title}</div>
      <div class="insight-text">${i.text}</div>
    </div>
  `).join('');
}

// Check OPC connection status
async function checkOPCStatus() {
  try {
    const response = await fetch('http://localhost:5055/api/v1/health', {
      method: 'GET',
      timeout: 2000
    });

    if (response.ok) {
      document.getElementById('sync-status').textContent = '已连接OPC';
      document.getElementById('sync-status').style.color = '#34c759';
    } else {
      throw new Error('Not OK');
    }
  } catch (error) {
    document.getElementById('sync-status').textContent = '仅本地存储';
    document.getElementById('sync-status').style.color = '#999';
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Initial load
  updateCurrentActivity();
  updateTodayStats();
  checkOPCStatus();

  // Refresh every 5 seconds
  setInterval(() => {
    updateCurrentActivity();
    updateTodayStats();
  }, 5000);

  // Check OPC status every 30 seconds
  setInterval(checkOPCStatus, 30000);
});
