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
