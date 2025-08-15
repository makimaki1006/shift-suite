// C2 モバイル対応統合JavaScript - Phase5最終版
// 自動生成日時: 2025-08-03 23:24:40

(function() {
  'use strict';
  
  // C2モバイル強化モジュール
  window.C2MobileEnhancement = window.C2MobileEnhancement || {};
  
  // 初期化フラグ
  let initialized = false;
  
  // 統合初期化関数
  window.C2MobileEnhancement.init = function() {
    if (initialized) return;
    initialized = true;
    
    console.log('C2 Mobile Enhancement initializing...');
    

    // ========== c2-touch-enhancements.js ==========
    // touch_enhancements モジュール
    try {
      // C2 タッチ操作改善 - Phase2
      // 既存JavaScriptに影響しない追加機能
      // タッチ操作最適化関数
      function c2OptimizeTouchInteraction() {
          // タッチターゲットサイズ確保
          const touchElements = document.querySelectorAll('button, a, .dash-table-container');
          touchElements.forEach(element => {
              const rect = element.getBoundingClientRect();
              if (rect.width < 44 || rect.height < 44) {
                  element.classList.add('c2-touch-friendly');
              }
          });
          // スクロール領域最適化
          const scrollContainers = document.querySelectorAll('.dash-table-container, .plotly-graph-div');
          scrollContainers.forEach(container => {
              container.classList.add('c2-mobile-scroll');
          });
      }
      // モバイルデバイス検出時のみ実行
      if (window.innerWidth <= 768) {
          // DOMロード後に実行
          if (document.readyState === 'loading') {
              document.addEventListener('DOMContentLoaded', c2OptimizeTouchInteraction);
          } else {
              c2OptimizeTouchInteraction();
          }
          // 動的コンテンツ更新時の再適用
          const observer = new MutationObserver(function(mutations) {
              let shouldOptimize = false;
              mutations.forEach(function(mutation) {
                  if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                      shouldOptimize = true;
                  }
              });
              if (shouldOptimize) {
                  setTimeout(c2OptimizeTouchInteraction, 100);
              }
          });
          observer.observe(document.body, {
              childList: true,
              subtree: true
          });
      }
      console.log('touch_enhancements loaded successfully');
    } catch(e) {
      console.error('touch_enhancements error:', e);
    }

    // ========== c2-mobile-shortcuts.js ==========
    // mobile_shortcuts モジュール
    try {
      // C2 Phase4: モバイルショートカット
      // 既存操作を妨げない追加ジェスチャー
        // モバイルのみ実行
        if (window.innerWidth > 768) return;
        // ダブルタップでトップへ
        let lastTap = 0;
        document.addEventListener('touchend', function(e) {
          const currentTime = new Date().getTime();
          const tapLength = currentTime - lastTap;
          if (tapLength < 500 && tapLength > 0) {
            // ヘッダー部分のダブルタップのみ
            if (e.target.closest('.dash-header, .c2-mobile-header')) {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }
          }
          lastTap = currentTime;
        });
        // スワイプでタブ切り替え（タブエリアのみ）
        let touchStartX = 0;
        let touchEndX = 0;
        const tabContainer = document.querySelector('.dash-tabs, .c2-mobile-tabs');
        if (tabContainer) {
          tabContainer.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
          });
          tabContainer.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
          });
        }
        function handleSwipe() {
          const swipeDistance = touchEndX - touchStartX;
          const minSwipeDistance = 50;
          if (Math.abs(swipeDistance) < minSwipeDistance) return;
          // 左スワイプ: 次のタブ
          if (swipeDistance < -minSwipeDistance) {
            navigateTab('next');
          }
          // 右スワイプ: 前のタブ
          else if (swipeDistance > minSwipeDistance) {
            navigateTab('prev');
          }
        }
        function navigateTab(direction) {
          const tabs = document.querySelectorAll('.dash-tab, .c2-mobile-tab-item');
          const activeTab = document.querySelector('.dash-tab--selected, .c2-mobile-tab-item.active');
          if (!tabs.length || !activeTab) return;
          const currentIndex = Array.from(tabs).indexOf(activeTab);
          let nextIndex;
          if (direction === 'next') {
            nextIndex = (currentIndex + 1) % tabs.length;
          } else {
            nextIndex = currentIndex - 1 < 0 ? tabs.length - 1 : currentIndex - 1;
          }
          // タブクリックをシミュレート
          if (tabs[nextIndex]) {
            tabs[nextIndex].click();
          }
        }
        // 長押しでコンテキストメニュー（将来拡張用）
        let pressTimer;
        document.addEventListener('touchstart', function(e) {
          pressTimer = setTimeout
            // データテーブルセルの長押し
            if (e.target.closest('.dash-cell')) {
              e.preventDefault();
              // 将来的にコンテキストメニュー実装
              console.log('Long press detected on table cell');
            }
          }, 800);
        });
        document.addEventListener('touchend', function() {
          clearTimeout(pressTimer);
        });
        // ピンチズームの制御（チャートエリアのみ許可）
        document.addEventListener('gesturestart', function(e) {
          if (!e.target.closest('.plotly-graph-div')) {
            e.preventDefault();
          }
        });
      console.log('mobile_shortcuts loaded successfully');
    } catch(e) {
      console.error('mobile_shortcuts error:', e);
    }

    // ========== c2-performance-optimization.js ==========
    // performance_optimization モジュール
    try {
      // C2 Phase4: パフォーマンス最適化
      // 重いコンポーネントの遅延読み込み
        // Intersection Observer で遅延読み込み
        if ('IntersectionObserver' in window) {
          const lazyComponents = document.querySelectorAll('.dash-graph, .dash-table-container');
          const componentObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
              if (entry.isIntersecting) {
                const component = entry.target;
                // コンポーネント表示時に初期化
                component.classList.add('c2-loaded');
                // 一度読み込んだら監視解除
                componentObserver.unobserve(component);
              }
            });
          }, {
            rootMargin: '50px'
          });
          lazyComponents.forEach(function(component) {
            componentObserver.observe(component);
          });
        }
        // デバウンス処理でイベント最適化
        function debounce(func, wait) {
          let timeout;
          return function executedFunction(...args) {
            const later = () => {
              clearTimeout(timeout);
              func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
          };
        }
        // スクロールイベント最適化
        const optimizedScroll = debounce
          // スクロール位置に基づく処理
          const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
          // モバイルのみ: 一定以上スクロールしたらヘッダー縮小
          if (window.innerWidth <= 768) {
            const header = document.querySelector('.dash-header, .c2-mobile-header');
            if (header) {
              if (scrollPosition > 100) {
                header.classList.add('c2-compact');
              } else {
                header.classList.remove('c2-compact');
              }
            }
          }
        }, 100);
        window.addEventListener('scroll', optimizedScroll, { passive: true });
        // リサイズイベント最適化
        const optimizedResize = debounce
          // Plotlyチャートのリサイズ
          const plots = document.querySelectorAll('.plotly-graph-div');
          plots.forEach(function(plot) {
            if (window.Plotly && plot.data) {
              window.Plotly.Plots.resize(plot);
            }
          });
        }, 300);
        window.addEventListener('resize', optimizedResize);
        // 画像の遅延読み込み（将来の画像追加に備えて）
        if ('loading' in HTMLImageElement.prototype) {
          const images = document.querySelectorAll('img[data-src]');
          images.forEach(img => {
            img.loading = 'lazy';
            if (img.dataset.src) {
              img.src = img.dataset.src;
            }
          });
        }
        // RequestIdleCallback で非優先処理
        if ('requestIdleCallback' in window) {
          requestIdleCallback
            // 非優先的な初期化処理
            console.log('C2 Performance optimizations loaded');
          });
        }
      console.log('performance_optimization loaded successfully');
    } catch(e) {
      console.error('performance_optimization error:', e);
    }

    console.log('C2 Mobile Enhancement initialized successfully');
  };
  
  // 自動初期化（DOMロード後）
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.C2MobileEnhancement.init);
  } else {
    window.C2MobileEnhancement.init();
  }
  
})();
