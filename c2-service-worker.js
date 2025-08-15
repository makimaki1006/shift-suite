// C2 Phase4: 最小限のオフライン対応
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
