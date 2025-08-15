// C2 Phase4: モバイルショートカット
// 既存操作を妨げない追加ジェスチャー

(function() {
  'use strict';
  
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
    pressTimer = setTimeout(function() {
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
  
})();
