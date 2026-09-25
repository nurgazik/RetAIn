import SwiftUI
import WebKit

struct PieceWebView: UIViewRepresentable {
    let html: String
    var onTap: ((String) -> Void)? = nil

    func makeCoordinator() -> Coordinator { Coordinator(onTap: onTap) }
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(context.coordinator, name: "tap")
        let w = WKWebView(frame: .zero, configuration: cfg)
        w.isOpaque = false
        w.loadHTMLString(html, baseURL: nil)
        return w
    }
    func updateUIView(_ uiView: WKWebView, context: Context) { context.coordinator.onTap = onTap }

    final class Coordinator: NSObject, WKScriptMessageHandler {
        var onTap: ((String) -> Void)?
        init(onTap: ((String) -> Void)?) { self.onTap = onTap }
        func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) {
            if let w = message.body as? String { onTap?(w) }
        }
    }
}
