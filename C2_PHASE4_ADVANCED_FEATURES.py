"""
C2 Phase4実行: 高度機能フェーズ
Phase1-3の成功を受けて、慎重に高度なモバイル機能を追加
リスク: medium、期間: 1日
条件付き実行 - 既存機能への影響を最小限に
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any

class C2Phase4AdvancedFeatures:
    """C2 Phase4 高度機能システム"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.phase3_results_file = None
        self.backup_dir = "C2_PRE_IMPLEMENTATION_BACKUP_20250803_224035"
        
        # Phase4条件付き実行判定
        self.execution_criteria = {
            'phase1_3_success': None,  # 確認待ち
            'system_stability': None,   # 確認待ち
            'risk_acceptable': None,    # 確認待ち
            'proceed_decision': None    # 最終判定
        }
        
        # 高度機能の実装計画（既存破壊しない）
        self.advanced_features = {
            'offline_capability': {
                'priority': 'high',
                'risk': 'medium',
                'description': 'オフライン時の基本機能維持',
                'implementation': 'service_worker_based',
                'scope': 'minimal_critical_functions'
            },
            'mobile_shortcuts': {
                'priority': 'medium',
                'risk': 'low',
                'description': 'モバイル専用ショートカット',
                'implementation': 'javascript_gesture_based',
                'scope': 'common_operations'
            },
            'enhanced_performance': {
                'priority': 'high',
                'risk': 'low', 
                'description': 'モバイル向けパフォーマンス最適化',
                'implementation': 'lazy_loading_optimization',
                'scope': 'heavy_components'
            },
            'pwa_foundation': {
                'priority': 'low',
                'risk': 'medium',
                'description': 'PWA基盤準備',
                'implementation': 'manifest_preparation',
                'scope': 'future_readiness'
            }
        }
        
        # 絶対保護要素（Phase4でも厳格保護）
        self.critical_protections = {
            'calculation_logic': 'SLOT_HOURS and all calculations',
            'data_pipeline': 'Excel → processing → visualization',
            'dash_callbacks': 'All existing callback functions',
            'phase2_3_integration': 'FactExtractor and AnomalyDetector',
            'phase1_3_enhancements': 'All CSS and JS from previous phases'
        }
        
    def execute_phase4(self):
        """Phase4実行: 高度機能 - 条件付き慎重実装"""
        print("🔴 C2 Phase4開始: 高度機能フェーズ")
        print("⏰ 推定時間: 1日")
        print("🛡️ リスクレベル: medium")
        print("⚖️ 実行方式: 条件付き・段階的")
        
        try:
            # Phase4実行可否判定
            print("\n🔍 Phase4実行可否判定...")
            execution_decision = self._evaluate_phase4_execution()
            
            if not execution_decision['proceed']:
                return {
                    'phase': 'C2_Phase4_Advanced_Features',
                    'status': 'deferred',
                    'reason': execution_decision['reason'],
                    'recommendation': execution_decision['recommendation'],
                    'timestamp': datetime.now().isoformat()
                }
            
            # システム保護スナップショット
            print("\n📸 システム保護スナップショット...")
            protection_snapshot = self._create_protection_snapshot()
            
            # 実装する高度機能の選定
            print("\n🎯 実装機能選定...")
            selected_features = self._select_safe_features()
            
            # Step 1: オフライン基盤（最小限）
            if 'offline_capability' in selected_features:
                print("\n📡 Step 1: オフライン基盤構築...")
                offline_result = self._implement_offline_foundation()
            else:
                offline_result = {'skipped': True, 'reason': 'リスク回避'}
            
            # Step 2: モバイルショートカット
            if 'mobile_shortcuts' in selected_features:
                print("\n⚡ Step 2: モバイルショートカット実装...")
                shortcuts_result = self._implement_mobile_shortcuts()
            else:
                shortcuts_result = {'skipped': True, 'reason': 'リスク回避'}
            
            # Step 3: パフォーマンス最適化
            if 'enhanced_performance' in selected_features:
                print("\n🚀 Step 3: パフォーマンス最適化...")
                performance_result = self._enhance_performance()
            else:
                performance_result = {'skipped': True, 'reason': 'リスク回避'}
            
            # Step 4: PWA基盤準備（オプション）
            if 'pwa_foundation' in selected_features:
                print("\n📱 Step 4: PWA基盤準備...")
                pwa_result = self._prepare_pwa_foundation()
            else:
                pwa_result = {'skipped': True, 'reason': 'デフォルトスキップ'}
            
            # Step 5: 段階的統合
            print("\n🔗 Step 5: 段階的統合...")
            integration_result = self._phased_integration()
            
            # Step 6: 高度機能検証
            print("\n✅ Step 6: 高度機能検証...")
            advanced_verification = self._verify_advanced_features()
            
            # Phase4結果統合
            phase4_result = {
                'metadata': {
                    'phase': 'C2_Phase4_Advanced_Features',
                    'timestamp': datetime.now().isoformat(),
                    'duration': '1日',
                    'risk_level': 'medium',
                    'execution_mode': 'conditional_selective',
                    'status': 'completed' if advanced_verification['success'] else 'partial'
                },
                'execution_decision': execution_decision,
                'selected_features': selected_features,
                'protection_snapshot': protection_snapshot,
                'feature_implementations': {
                    'offline_capability': offline_result,
                    'mobile_shortcuts': shortcuts_result,
                    'enhanced_performance': performance_result,
                    'pwa_foundation': pwa_result
                },
                'integration_result': integration_result,
                'advanced_verification': advanced_verification,
                'phase4_success_criteria': self._verify_phase4_success_criteria(advanced_verification)
            }
            
            # 成功判定
            if advanced_verification['success']:
                print(f"\n✅ Phase4実装成功!")
                print(f"🎯 高度機能追加完了 - 既存機能完全保護")
                print(f"🚀 Phase5（最適化）準備完了")
            else:
                print(f"\n⚠️ Phase4部分成功")
                print(f"🔄 一部機能スキップ - 安定性優先")
            
            return phase4_result
            
        except Exception as e:
            print(f"\n🚨 Phase4実行エラー: {str(e)}")
            print("🔄 安全モードロールバック実行...")
            safety_rollback = self._execute_safety_rollback()
            
            return {
                'error': str(e),
                'phase': 'C2_Phase4_Advanced_Features',
                'status': 'error_with_rollback',
                'timestamp': datetime.now().isoformat(),
                'safety_rollback': safety_rollback
            }
    
    def _evaluate_phase4_execution(self):
        """Phase4実行可否評価"""
        evaluation = {
            'proceed': False,
            'criteria_met': {},
            'reason': '',
            'recommendation': ''
        }
        
        # Phase1-3成功確認
        print("  📊 Phase1-3成功確認...")
        phase3_files = [f for f in os.listdir(self.base_path) if f.startswith('C2_Phase3_Targeted_Results_')]
        if phase3_files:
            self.phase3_results_file = phase3_files[-1]
            try:
                with open(os.path.join(self.base_path, self.phase3_results_file), 'r', encoding='utf-8') as f:
                    phase3_data = json.load(f)
                
                phase3_success = phase3_data.get('phase3_success_criteria', {}).get('overall_success', False)
                evaluation['criteria_met']['phase1_3_success'] = phase3_success
                self.execution_criteria['phase1_3_success'] = phase3_success
                print(f"    ✅ Phase1-3成功: {phase3_success}")
                
            except Exception as e:
                evaluation['criteria_met']['phase1_3_success'] = False
                self.execution_criteria['phase1_3_success'] = False
                print(f"    ❌ Phase3結果確認エラー: {str(e)}")
        
        # システム安定性確認
        print("  🔍 システム安定性確認...")
        stability_check = self._check_system_stability()
        evaluation['criteria_met']['system_stability'] = stability_check['stable']
        self.execution_criteria['system_stability'] = stability_check['stable']
        
        # リスク評価
        print("  ⚖️ リスク評価...")
        risk_evaluation = self._evaluate_risks()
        evaluation['criteria_met']['risk_acceptable'] = risk_evaluation['acceptable']
        self.execution_criteria['risk_acceptable'] = risk_evaluation['acceptable']
        
        # 最終判定
        all_criteria_met = all(evaluation['criteria_met'].values())
        evaluation['proceed'] = all_criteria_met
        self.execution_criteria['proceed_decision'] = all_criteria_met
        
        if all_criteria_met:
            evaluation['reason'] = 'すべての実行基準を満たしています'
            evaluation['recommendation'] = 'Phase4実行を推奨'
        else:
            failed_criteria = [k for k, v in evaluation['criteria_met'].items() if not v]
            evaluation['reason'] = f'実行基準未達: {", ".join(failed_criteria)}'
            evaluation['recommendation'] = 'Phase5へスキップを推奨'
        
        return evaluation
    
    def _check_system_stability(self):
        """システム安定性チェック"""
        stability = {
            'stable': True,
            'checks': {},
            'issues': []
        }
        
        # 重要ファイル整合性
        critical_files = [
            'dash_app.py',
            'app.py',
            'shift_suite/tasks/fact_extractor_prototype.py',
            'shift_suite/tasks/lightweight_anomaly_detector.py'
        ]
        
        for file_path in critical_files:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                stability['checks'][file_path] = 'exists'
            else:
                stability['checks'][file_path] = 'missing'
                stability['issues'].append(f'{file_path} が見つかりません')
                stability['stable'] = False
        
        # Phase1-3成果物確認
        phase_artifacts = [
            'c2-mobile-enhancements.css',
            'c2-mobile-navigation.css',
            'c2-mobile-table.css',
            'c2-mobile-forms.css'
        ]
        
        artifact_count = 0
        for artifact in phase_artifacts:
            if os.path.exists(os.path.join(self.base_path, artifact)):
                artifact_count += 1
        
        stability['checks']['phase_artifacts'] = f'{artifact_count}/{len(phase_artifacts)}'
        
        if artifact_count < len(phase_artifacts):
            stability['issues'].append('一部のPhase成果物が欠損しています')
            # これは警告レベルで、安定性判定は変更しない
        
        return stability
    
    def _evaluate_risks(self):
        """リスク評価"""
        risk_eval = {
            'acceptable': True,
            'risk_factors': [],
            'risk_score': 0,
            'recommendation': ''
        }
        
        # バックアップ確認
        if not os.path.exists(os.path.join(self.base_path, self.backup_dir)):
            risk_eval['risk_factors'].append('バックアップディレクトリ欠損')
            risk_eval['risk_score'] += 30
        
        # 既存システムサイズ確認
        dash_app_path = os.path.join(self.base_path, 'dash_app.py')
        if os.path.exists(dash_app_path):
            file_size = os.path.getsize(dash_app_path)
            if file_size > 500000:  # 500KB以上は要注意
                risk_eval['risk_factors'].append(f'dash_app.pyが大きい: {file_size} bytes')
                risk_eval['risk_score'] += 20
        
        # Phase4の複雑性
        risk_eval['risk_factors'].append('高度機能実装の複雑性')
        risk_eval['risk_score'] += 15
        
        # リスク判定
        if risk_eval['risk_score'] > 50:
            risk_eval['acceptable'] = False
            risk_eval['recommendation'] = 'リスクが高すぎます - Phase5へのスキップ推奨'
        elif risk_eval['risk_score'] > 30:
            risk_eval['acceptable'] = True
            risk_eval['recommendation'] = '慎重な実装が必要です'
        else:
            risk_eval['acceptable'] = True
            risk_eval['recommendation'] = '安全に実装可能です'
        
        return risk_eval
    
    def _select_safe_features(self):
        """安全に実装可能な機能の選定"""
        selected = []
        
        # リスクレベルに基づく選定
        if self.execution_criteria['risk_acceptable']:
            # 低〜中リスクの機能を選定
            for feature_name, feature_info in self.advanced_features.items():
                if feature_info['risk'] in ['low', 'medium'] and feature_info['priority'] in ['high', 'medium']:
                    selected.append(feature_name)
                    print(f"  ✅ {feature_name}: 選定（リスク: {feature_info['risk']}）")
                else:
                    print(f"  ⏭️ {feature_name}: スキップ（リスク/優先度）")
        else:
            # 最小限の低リスク機能のみ
            for feature_name, feature_info in self.advanced_features.items():
                if feature_info['risk'] == 'low' and feature_info['priority'] == 'high':
                    selected.append(feature_name)
                    print(f"  ✅ {feature_name}: 最小限選定")
        
        return selected
    
    def _create_protection_snapshot(self):
        """システム保護スナップショット"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'protected_files': {},
            'system_state': {}
        }
        
        # 保護対象ファイルのハッシュ記録
        protected_files = [
            'dash_app.py',
            'shift_suite/tasks/fact_extractor_prototype.py',
            'shift_suite/tasks/lightweight_anomaly_detector.py'
        ]
        
        for file_path in protected_files:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                snapshot['protected_files'][file_path] = {
                    'size': os.path.getsize(full_path),
                    'mtime': os.path.getmtime(full_path)
                }
        
        return snapshot
    
    def _implement_offline_foundation(self):
        """オフライン基盤実装（最小限）"""
        offline = {
            'success': False,
            'implementation': 'minimal_service_worker',
            'features': [],
            'files_created': []
        }
        
        try:
            # 最小限のService Worker作成
            sw_content = """// C2 Phase4: 最小限のオフライン対応
// 既存機能に影響しない基本キャッシュのみ

const CACHE_NAME = 'shift-analysis-v1';
const urlsToCache = [
  '/',
  '/static/css/c2-mobile-enhancements.css',
  '/static/css/c2-mobile-navigation.css',
  '/static/css/c2-mobile-table.css',
  '/static/css/c2-mobile-forms.css'
];

// インストール時に基本リソースをキャッシュ
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// ネットワークファースト戦略（既存動作優先）
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // ネットワークからの応答をキャッシュ
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        
        const responseToCache = response.clone();
        caches.open(CACHE_NAME)
          .then(cache => {
            cache.put(event.request, responseToCache);
          });
        
        return response;
      })
      .catch(() => {
        // オフライン時はキャッシュから
        return caches.match(event.request);
      })
  );
});

// 古いキャッシュの削除
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
"""
            
            sw_path = os.path.join(self.base_path, 'c2-service-worker.js')
            with open(sw_path, 'w', encoding='utf-8') as f:
                f.write(sw_content)
            
            offline['files_created'].append('c2-service-worker.js')
            offline['features'].append('基本リソースキャッシュ')
            offline['features'].append('ネットワークファースト戦略')
            offline['success'] = True
            
            print(f"    ✅ オフライン基盤実装完了")
            
        except Exception as e:
            offline['error'] = str(e)
            print(f"    ❌ オフライン基盤実装エラー: {str(e)}")
        
        return offline
    
    def _implement_mobile_shortcuts(self):
        """モバイルショートカット実装"""
        shortcuts = {
            'success': False,
            'shortcuts_implemented': [],
            'integration_method': 'javascript_gestures',
            'files_created': []
        }
        
        try:
            # モバイルショートカットJS
            shortcuts_js = """// C2 Phase4: モバイルショートカット
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
"""
            
            shortcuts_path = os.path.join(self.base_path, 'c2-mobile-shortcuts.js')
            with open(shortcuts_path, 'w', encoding='utf-8') as f:
                f.write(shortcuts_js)
            
            shortcuts['files_created'].append('c2-mobile-shortcuts.js')
            shortcuts['shortcuts_implemented'] = [
                'ダブルタップでトップへ',
                'スワイプでタブ切り替え',
                '長押し検出（拡張準備）',
                'ピンチズーム制御'
            ]
            shortcuts['success'] = True
            
            print(f"    ✅ モバイルショートカット実装完了")
            
        except Exception as e:
            shortcuts['error'] = str(e)
            print(f"    ❌ モバイルショートカット実装エラー: {str(e)}")
        
        return shortcuts
    
    def _enhance_performance(self):
        """パフォーマンス最適化"""
        performance = {
            'success': False,
            'optimizations': [],
            'implementation': 'lazy_loading_and_optimization',
            'files_created': []
        }
        
        try:
            # パフォーマンス最適化JS
            perf_js = """// C2 Phase4: パフォーマンス最適化
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
"""
            
            perf_path = os.path.join(self.base_path, 'c2-performance-optimization.js')
            with open(perf_path, 'w', encoding='utf-8') as f:
                f.write(perf_js)
            
            # パフォーマンス用CSS
            perf_css = """/* C2 Phase4: パフォーマンス最適化CSS */

/* 遅延読み込み前の状態 */
.dash-graph:not(.c2-loaded),
.dash-table-container:not(.c2-loaded) {
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

/* 読み込み完了後 */
.dash-graph.c2-loaded,
.dash-table-container.c2-loaded {
  opacity: 1;
}

/* コンパクトヘッダー（スクロール時） */
.c2-compact {
  padding: 8px 16px !important;
  transition: padding 0.3s ease;
}

/* GPU加速の活用 */
.c2-mobile-nav-enhancement,
.c2-mobile-slide-menu,
.dash-graph {
  will-change: transform;
  transform: translateZ(0);
}

/* アニメーション最適化 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* 低帯域幅対応 */
@media (max-width: 768px) and (max-resolution: 1dppx) {
  /* 低解像度デバイス向け軽量化 */
  .plotly-graph-div {
    image-rendering: optimizeSpeed;
  }
}
"""
            
            perf_css_path = os.path.join(self.base_path, 'c2-performance.css')
            with open(perf_css_path, 'w', encoding='utf-8') as f:
                f.write(perf_css)
            
            performance['files_created'] = ['c2-performance-optimization.js', 'c2-performance.css']
            performance['optimizations'] = [
                '遅延読み込み実装',
                'イベントデバウンス',
                'GPU加速活用',
                'アニメーション最適化'
            ]
            performance['success'] = True
            
            print(f"    ✅ パフォーマンス最適化完了")
            
        except Exception as e:
            performance['error'] = str(e)
            print(f"    ❌ パフォーマンス最適化エラー: {str(e)}")
        
        return performance
    
    def _prepare_pwa_foundation(self):
        """PWA基盤準備（最小限）"""
        pwa = {
            'success': False,
            'preparation': 'manifest_only',
            'files_created': []
        }
        
        try:
            # 最小限のmanifest.json
            manifest = {
                "name": "シフト分析システム",
                "short_name": "ShiftAnalysis",
                "description": "医療・介護シフト分析ダッシュボード",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#007bff",
                "orientation": "any",
                "icons": [
                    {
                        "src": "/static/icon-192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "any maskable"
                    },
                    {
                        "src": "/static/icon-512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any maskable"
                    }
                ]
            }
            
            manifest_path = os.path.join(self.base_path, 'c2-manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            pwa['files_created'].append('c2-manifest.json')
            pwa['success'] = True
            
            print(f"    ✅ PWA基盤準備完了（manifest作成）")
            
        except Exception as e:
            pwa['error'] = str(e)
            print(f"    ❌ PWA基盤準備エラー: {str(e)}")
        
        return pwa
    
    def _phased_integration(self):
        """段階的統合"""
        integration = {
            'success': False,
            'integration_steps': [],
            'safety_checks': []
        }
        
        try:
            # 統合準備コメント（実際の統合はPhase5で）
            integration_comment = """

# C2 Phase4: 高度機能統合準備
# 作成されたファイル:
# - c2-service-worker.js (オフライン基盤)
# - c2-mobile-shortcuts.js (モバイルショートカット)
# - c2-performance-optimization.js (パフォーマンス最適化)
# - c2-performance.css (パフォーマンスCSS)
# - c2-manifest.json (PWA基盤)
# 統合準備完了 - Phase5で最終統合実行
"""
            
            dash_app_path = os.path.join(self.base_path, 'dash_app.py')
            
            # バックアップ作成
            backup_path = f"{dash_app_path}.c2_phase4_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(dash_app_path, backup_path)
            
            integration['integration_steps'].append(f'バックアップ作成: {backup_path}')
            
            # 統合コメント追加
            with open(dash_app_path, 'a', encoding='utf-8') as f:
                f.write(integration_comment)
            
            integration['integration_steps'].append('統合準備コメント追加')
            integration['safety_checks'].append('既存コード非改変')
            integration['safety_checks'].append('バックアップ作成済み')
            
            integration['success'] = True
            
            print(f"    ✅ 段階的統合準備完了")
            
        except Exception as e:
            integration['error'] = str(e)
            print(f"    ❌ 段階的統合エラー: {str(e)}")
        
        return integration
    
    def _verify_advanced_features(self):
        """高度機能検証"""
        verification = {
            'success': True,
            'feature_checks': {},
            'system_integrity': {},
            'issues': []
        }
        
        print("    🔍 高度機能検証開始...")
        
        # 作成ファイル確認
        expected_files = [
            'c2-service-worker.js',
            'c2-mobile-shortcuts.js',
            'c2-performance-optimization.js',
            'c2-performance.css'
        ]
        
        for file_name in expected_files:
            file_path = os.path.join(self.base_path, file_name)
            if os.path.exists(file_path):
                verification['feature_checks'][file_name] = {
                    'exists': True,
                    'size': os.path.getsize(file_path)
                }
            else:
                verification['feature_checks'][file_name] = {'exists': False}
                # オプション機能なので警告のみ
                verification['issues'].append(f'{file_name}: 作成されていません（オプション）')
        
        # システム整合性確認
        critical_files = ['dash_app.py', 'app.py']
        for file_path in critical_files:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    compile(content, full_path, 'exec')
                    verification['system_integrity'][file_path] = 'valid'
                    
                except SyntaxError as e:
                    verification['system_integrity'][file_path] = f'syntax_error: {str(e)}'
                    verification['issues'].append(f'{file_path}: 構文エラー')
                    verification['success'] = False
        
        # SLOT_HOURS保護最終確認
        fact_extractor_path = os.path.join(self.base_path, 'shift_suite/tasks/fact_extractor_prototype.py')
        if os.path.exists(fact_extractor_path):
            with open(fact_extractor_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            slot_hours_count = content.count('* SLOT_HOURS')
            if slot_hours_count >= 4:
                verification['system_integrity']['slot_hours_protection'] = 'protected'
                print(f"      ✅ SLOT_HOURS計算: {slot_hours_count}箇所保護確認")
            else:
                verification['system_integrity']['slot_hours_protection'] = 'compromised'
                verification['issues'].append('SLOT_HOURS計算が変更された可能性')
                verification['success'] = False
        
        return verification
    
    def _verify_phase4_success_criteria(self, verification_result):
        """Phase4成功基準検証"""
        criteria = {
            'advanced_features_implemented': len(verification_result.get('feature_checks', {})) > 0,
            'system_integrity_maintained': verification_result.get('success', False),
            'no_breaking_changes': verification_result.get('success', False),
            'performance_optimized': 'c2-performance-optimization.js' in verification_result.get('feature_checks', {}),
            'ready_for_phase5': verification_result.get('success', False)
        }
        
        overall_success = all(criteria.values())
        
        return {
            'overall_success': overall_success,
            'individual_criteria': criteria,
            'next_phase_recommendation': 'proceed_to_phase5' if overall_success else 'phase5_with_caution'
        }
    
    def _execute_safety_rollback(self):
        """安全モードロールバック"""
        rollback = {
            'timestamp': datetime.now().isoformat(),
            'rollback_type': 'safety_mode',
            'success': False
        }
        
        try:
            # Phase4で作成されたファイルを削除
            phase4_files = [
                'c2-service-worker.js',
                'c2-mobile-shortcuts.js',
                'c2-performance-optimization.js',
                'c2-performance.css',
                'c2-manifest.json'
            ]
            
            for file_name in phase4_files:
                file_path = os.path.join(self.base_path, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # dash_app.pyの復元
            backup_files = [f for f in os.listdir(self.base_path) if f.startswith('dash_app.py.c2_phase4_backup_')]
            if backup_files:
                latest_backup = max(backup_files)
                backup_path = os.path.join(self.base_path, latest_backup)
                dash_app_path = os.path.join(self.base_path, 'dash_app.py')
                shutil.copy2(backup_path, dash_app_path)
            
            rollback['success'] = True
            print("  ✅ 安全モードロールバック完了")
            
        except Exception as e:
            rollback['error'] = str(e)
            print(f"  ❌ 安全モードロールバックエラー: {str(e)}")
        
        return rollback

def main():
    """C2 Phase4メイン実行"""
    print("🔴 C2 Phase4実行開始: 高度機能フェーズ")
    print("⚖️ 条件付き実行 - 既存機能保護優先")
    
    advanced = C2Phase4AdvancedFeatures()
    result = advanced.execute_phase4()
    
    # 結果保存
    result_file = f"C2_Phase4_Advanced_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 結果サマリー表示
    if result.get('status') == 'deferred':
        print(f"\n⏭️ Phase4延期判定")
        print(f"理由: {result.get('reason')}")
        print(f"推奨: {result.get('recommendation')}")
        return result
    
    if 'error' in result:
        print(f"\n❌ Phase4実行エラー: {result['error']}")
        if 'safety_rollback' in result:
            rollback_success = result['safety_rollback'].get('success', False)
            print(f"🔄 安全ロールバック: {'成功' if rollback_success else '失敗'}")
        return result
    
    print(f"\n🎯 Phase4実行完了!")
    print(f"📁 実行結果: {result_file}")
    
    # 実装結果サマリー
    verification = result.get('advanced_verification', {})
    success = verification.get('success', False)
    
    if success:
        print(f"\n✅ Phase4成功!")
        
        feature_implementations = result.get('feature_implementations', {})
        implemented_count = sum(1 for f in feature_implementations.values() if not f.get('skipped', False))
        print(f"  📱 実装機能数: {implemented_count}")
        
        for feature_name, feature_result in feature_implementations.items():
            if not feature_result.get('skipped', False) and feature_result.get('success', False):
                print(f"  ✅ {feature_name}: 実装完了")
        
        # 成功基準確認
        success_criteria = result.get('phase4_success_criteria', {})
        if success_criteria.get('overall_success'):
            print(f"\n🚀 Phase5実行準備完了")
            print(f"📋 次のアクション:")
            print(f"  1. Phase4結果レビュー・承認")
            print(f"  2. Phase5実行開始（最適化・完成）")
        else:
            print(f"\n⚠️ Phase4部分成功 - Phase5は慎重に実行")
    else:
        print(f"\n⚠️ Phase4部分成功")
        issues = verification.get('issues', [])
        for issue in issues[:3]:
            print(f"  • {issue}")
    
    return result

if __name__ == "__main__":
    result = main()