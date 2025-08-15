// C2 Phase4: パフォーマンス最適化
// 重いコンポーネントの遅延読み込み

(function() {
  'use strict';
  
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
  const optimizedScroll = debounce(function() {
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
  const optimizedResize = debounce(function() {
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
    requestIdleCallback(function() {
      // 非優先的な初期化処理
      console.log('C2 Performance optimizations loaded');
    });
  }
  
})();
