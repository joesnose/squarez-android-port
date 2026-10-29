package com.joesnose.squarez;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;
import android.webkit.JavascriptInterface;
import java.net.*;
import java.util.*;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import androidx.webkit.WebViewAssetLoader;

public class MainActivity extends Activity {
  private WebView web;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    getWindow().getDecorView().setSystemUiVisibility(5894 | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    web = new WebView(this);
    web.getSettings().setJavaScriptEnabled(true);
    web.addJavascriptInterface(new Object() {
      @JavascriptInterface public void discover() {
        new Thread(() -> {
          Set<String> hosts = new LinkedHashSet<>();
          try (DatagramSocket socket = new DatagramSocket()) {
            socket.setBroadcast(true);
            socket.setSoTimeout(450);
            byte[] query = "SQUAREZ_DISCOVER_V1".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()) {
              NetworkInterface iface = interfaces.nextElement();
              if (!iface.isUp() || iface.isLoopback()) continue;
              for (InterfaceAddress addr : iface.getInterfaceAddresses()) {
                if (addr.getBroadcast() == null) continue;
                socket.send(new DatagramPacket(query, query.length, addr.getBroadcast(), 38472));
              }
            }
            socket.send(new DatagramPacket(query, query.length, InetAddress.getByName("255.255.255.255"), 38472));
            long end = System.currentTimeMillis() + 2000;
            while (System.currentTimeMillis() < end) {
              try {
                byte[] buf = new byte[128];
                DatagramPacket packet = new DatagramPacket(buf, buf.length);
                socket.receive(packet);
                if (new String(packet.getData(), 0, packet.getLength(), java.nio.charset.StandardCharsets.UTF_8).trim().equals("SQUAREZ_HOST_V1")) hosts.add(packet.getAddress().getHostAddress());
              } catch (SocketTimeoutException ignored) { }
            }
          } catch (Exception ignored) { }
          StringBuilder json = new StringBuilder("[");
          for (String host : hosts) { if (json.length() > 1) json.append(','); json.append('"').append(host).append('"'); }
          json.append(']');
          web.post(() -> web.evaluateJavascript("window.squarezDiscoveryResult && window.squarezDiscoveryResult(" + json + ")", null));
        }).start();
      }
    }, "SquarezDiscovery");
    web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
    web.getSettings().setDomStorageEnabled(true);
    web.getSettings().setMediaPlaybackRequiresUserGesture(false);
    final WebViewAssetLoader loader = new WebViewAssetLoader.Builder().addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this)).build();
    web.setWebViewClient(new WebViewClient() {
      @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) { return loader.shouldInterceptRequest(request.getUrl()); }
    });
    setContentView(web);
    web.loadUrl("https://appassets.androidplatform.net/assets/index.html");
  }
  @Override public void onBackPressed() {
    web.evaluateJavascript("window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',code:'Escape',bubbles:true}));", null);
  }
  @Override protected void onDestroy() { web.destroy(); super.onDestroy(); }
}
