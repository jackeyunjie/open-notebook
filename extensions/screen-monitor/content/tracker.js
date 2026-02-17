/**
 * OPC Activity Monitor - Content Script
 *
 * Runs on each page to detect content type and user engagement.
 * Privacy-first: Only extracts content type, not actual content.
 */

(function() {
  'use strict';

  // Prevent double-injection
  if (window.opcTrackerInjected) return;
  window.opcTrackerInjected = true;

  // Content type detection
  function detectContentType() {
    const url = window.location.href;
    const title = document.title;

    // Video platforms
    if (url.includes('youtube.com/watch') || url.includes('bilibili.com/video')) {
      return detectVideoContent();
    }

    // Documentation/Reading
    if (url.includes('docs.') || url.includes('notion.') || url.includes('wiki')) {
      return 'documentation';
    }

    // Social feed
    if (url.includes('twitter.com') || url.includes('x.com/home') || url.includes('weibo.com')) {
      return 'social-feed';
    }

    // Code repositories
    if (url.includes('github.com') && url.split('/').length > 4) {
      return 'code-reading';
    }

    // Article/Writing
    const articleMarkers = document.querySelectorAll('article, [role="article"], .post-content, .entry-content');
    if (articleMarkers.length > 0) {
      return 'article-reading';
    }

    // Editor/Writing tool
    const editorMarkers = document.querySelectorAll('[contenteditable="true"], textarea, .editor');
    if (editorMarkers.length > 0) {
      return 'writing';
    }

    return 'general';
  }

  // Detect video content metadata (without collecting actual content)
  function detectVideoContent() {
    const isPlaying = !!document.querySelector('video');
    const hasProgressBar = !!document.querySelector('.ytp-progress-bar, .bilibili-player-video-progress');

    return {
      type: 'video',
      platform: window.location.hostname,
      isPlaying: isPlaying,
      hasProgressBar: hasProgressBar
    };
  }

  // Track scroll depth (engagement indicator)
  let maxScrollDepth = 0;

  function trackScrollDepth() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;

    if (docHeight > 0) {
      const depth = Math.round((scrollTop / docHeight) * 100);
      if (depth > maxScrollDepth) {
        maxScrollDepth = depth;
      }
    }
  }

  // Track copy events (learning indicator)
  let copyCount = 0;

  document.addEventListener('copy', () => {
    copyCount++;
    // User found something valuable enough to copy
    chrome.runtime.sendMessage({
      action: 'contentInteraction',
      type: 'copy',
      context: detectContentType()
    });
  });

  // Track selection (reading intensity)
  let selectionCount = 0;
  let lastSelectionTime = 0;

  document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (selection.toString().length > 10) {
      const now = Date.now();
      if (now - lastSelectionTime > 2000) { // Debounce
        selectionCount++;
        lastSelectionTime = now;
      }
    }
  });

  // Periodic engagement report
  setInterval(() => {
    const contentType = detectContentType();

    chrome.runtime.sendMessage({
      action: 'engagementReport',
      data: {
        url: window.location.href,
        contentType: contentType,
        scrollDepth: maxScrollDepth,
        copyCount: copyCount,
        selectionCount: selectionCount,
        timestamp: Date.now()
      }
    });

    // Reset for next period
    maxScrollDepth = 0;
    copyCount = 0;
    selectionCount = 0;

  }, 30000); // Every 30 seconds

  // Scroll listener
  let scrollTimeout;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(trackScrollDepth, 250);
  }, { passive: true });

  // Report initial page load
  chrome.runtime.sendMessage({
    action: 'pageLoaded',
    data: {
      url: window.location.href,
      title: document.title,
      contentType: detectContentType(),
      hasFavicon: !!document.querySelector('link[rel*="icon"]'),
      timestamp: Date.now()
    }
  });

  console.log('[OPC Monitor] Content tracker active on:', window.location.hostname);
})();