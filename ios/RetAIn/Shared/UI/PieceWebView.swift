import SwiftUI
import WebKit

/// The reader page; each highlight tap arrives in `onTap` with the word as printed, and each highlight
/// that has been at least half on screen for a second arrives once in `onSeen` (D74).
struct PieceWebView: UIViewRepresentable {
    let html: String
    var onTap: ((String) -> Void)? = nil
    var onSeen: ((String) -> Void)? = nil

    func makeCoordinator() -> Coordinator { Coordinator(onTap: onTap, onSeen: onSeen) }
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(context.coordinator, name: "tap")
        cfg.userContentController.add(context.coordinator, name: "seen")
        let w = WKWebView(frame: .zero, configuration: cfg)
        w.isOpaque = false
        w.loadHTMLString(html, baseURL: nil)
        return w
    }
    func updateUIView(_ uiView: WKWebView, context: Context) {
        context.coordinator.onTap = onTap
        context.coordinator.onSeen = onSeen
    }

    final class Coordinator: NSObject, WKScriptMessageHandler {
        var onTap: ((String) -> Void)?
        var onSeen: ((String) -> Void)?
        init(onTap: ((String) -> Void)?, onSeen: ((String) -> Void)?) { self.onTap = onTap; self.onSeen = onSeen }
        func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) {
            guard let w = message.body as? String else { return }
            if message.name == "seen" { onSeen?(w) } else { onTap?(w) }
        }
    }
}
