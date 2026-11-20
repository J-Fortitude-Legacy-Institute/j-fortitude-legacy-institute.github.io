/* JFLI approvals service worker.
 * Receives push events (sent payload-less via VAPID) and shows a generic
 * notification that opens /approvals when tapped. The page itself loads the
 * actual approval data via the user's own session — no payload ever crosses
 * the push network.
 */
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  event.waitUntil(
    self.registration.showNotification("Action waiting for approval", {
      body: "Tap to review the queued desktop action.",
      icon: "/favicon.ico",
      badge: "/favicon.ico",
      tag: "jfli-approval",
      renotify: true,
      requireInteraction: false,
      data: { url: "/approvals" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/approvals";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          client.navigate(target);
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(target);
      }
    })
  );
});
