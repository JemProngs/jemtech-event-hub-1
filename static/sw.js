const CACHE_NAME = 'jemtech-event-hub-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/css/dark-mode.css',
  '/static/css/collage-builder.css',
  '/static/js/script.js',
  '/static/js/upload.js',
  '/static/js/scanner.js',
  '/static/js/collage-editor.js',
  '/static/js/filters.js',
  '/static/images/hero-bg.jpg',
  '/static/images/hero-bg-dark.jpg',
  '/static/images/icons/icon-72x72.png',
  '/static/images/icons/icon-192x192.png'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Background sync for offline uploads
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-upload') {
    event.waitUntil(uploadPendingMedia());
  }
});

// Periodic sync for background updates
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'content-update') {
    event.waitUntil(updateCachedContent());
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/static/images/icons/icon-192x192.png',
      badge: '/static/images/icons/icon-72x72.png',
      vibrate: [100, 50, 100],
      data: {
        url: data.url
      }
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});

// Upload pending media when back online
async function uploadPendingMedia() {
  const pendingUploads = await getPendingUploads();

  for (const upload of pendingUploads) {
    try {
      const formData = new FormData();
      for (const [key, value] of Object.entries(upload.formData)) {
        formData.append(key, value);
      }

      // Add the file from storage
      const file = await getFileFromStorage(upload.fileKey);
      formData.append('file', file);

      const response = await fetch(upload.url, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        // Remove from pending uploads
        await removePendingUpload(upload.id);
      }
    } catch (error) {
      console.error('Failed to upload pending media:', error);
    }
  }
}

// Helper functions for offline storage
async function getPendingUploads() {
  // Implementation would use IndexedDB
  return [];
}

async function getFileFromStorage(key) {
  // Implementation would use the Cache API or IndexedDB
  return null;
}

async function removePendingUpload(id) {
  // Implementation would use IndexedDB
}

async function updateCachedContent() {
  // Update cached content in the background
  const cache = await caches.open(CACHE_NAME);

  for (const url of urlsToCache) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        await cache.put(url, response);
      }
    } catch (error) {
      console.error('Failed to update cached content:', error);
    }
  }
}