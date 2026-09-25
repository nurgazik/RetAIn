import UIKit
import SwiftUI

/// Principal class for BOTH the share extension and the action extension (same code, two
/// extension points). Presents SheetView immediately; input is gathered asynchronously.
final class ShareViewController: UIViewController {
    private let t0 = Date()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        let source = (Bundle.main.bundleIdentifier ?? "").hasSuffix("action") ? "action-ext" : "share-ext"
        Task { @MainActor in
            let input = await ExtensionInput.gather(from: extensionContext, source: source)
            let launchMs = Int(Date().timeIntervalSince(t0) * 1000)
            let host = UIHostingController(rootView: SheetView(input: input, launchMs: launchMs) { [weak self] in
                self?.extensionContext?.completeRequest(returningItems: nil)
            })
            addChild(host)
            host.view.frame = view.bounds
            host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            view.addSubview(host.view)
            host.didMove(toParent: self)
        }
    }
}
