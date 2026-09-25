import SwiftUI
import WebKit

struct PieceWebView: UIViewRepresentable {
    let html: String
    var onTap: ((String) -> Void)? = nil
    var onRetain: ((String) -> Void)? = nil

    func makeCoordinator() -> Coordinator { Coordinator(onTap: onTap, onRetain: onRetain) }
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(context.coordinator, name: "tap")
        cfg.userContentController.add(context.coordinator, name: "retain")
        let w = WKWebView(frame: .zero, configuration: cfg)
        w.isOpaque = false
        w.loadHTMLString(html, baseURL: nil)
        return w
    }
    func updateUIView(_ uiView: WKWebView, context: Context) { context.coordinator.onTap = onTap; context.coordinator.onRetain = onRetain }

    final class Coordinator: NSObject, WKScriptMessageHandler {
        var onTap: ((String) -> Void)?
        var onRetain: ((String) -> Void)?
        init(onTap: ((String) -> Void)?, onRetain: ((String) -> Void)?) { self.onTap = onTap; self.onRetain = onRetain }
        func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) {
            guard let w = message.body as? String else { return }
            if message.name == "retain" { onRetain?(w) } else { onTap?(w) }
        }
    }
}
