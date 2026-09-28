import SwiftUI
import UIKit

/// Principal class for both the share extension and the Safari action. No login here:
/// the session token comes from the app-group keychain. What a share means is the
/// ShareRouter's job (Shared/Sharing/): a word → capture, readable text → the transform sheet.
final class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        let source = (Bundle.main.bundleIdentifier ?? "").hasSuffix("action") ? "action-ext" : "share-ext"
        Task { @MainActor in
            show(AnyView(ProgressView("Reading the page…")))  // a link-only share takes a few seconds
            let input = await ShareInput.gather(from: extensionContext, source: source)
            let done: () -> Void = { [weak self] in self?.extensionContext?.completeRequest(returningItems: nil) }
            let root: AnyView
            if !SessionStore.isSignedIn {
                root = AnyView(MessageView(title: "Open RetAIn once to sign in", detail: "Then sharing works from anywhere.", onDone: done))
            } else {
                switch await ShareRouter().route(input) {
                case .capture(let word):
                    root = AnyView(CaptureView(word: word, onDone: done))
                case .read(let read, let reader):
                    let meta: [String: Any] = ["types": input.typeLog, "reader": reader, "extractor": read.extractor,
                                               "textChars": read.text.count,
                                               "build": Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "?"]
                    root = AnyView(SheetView(text: read.text, title: read.title, url: read.url ?? input.url, source: source,
                                             meta: meta, sourceFields: read.sourceFields, notice: read.notice, onDone: done))
                case .unusable(let title, let detail, let reader):
                    root = AnyView(MessageView(title: title, detail: detail, onDone: done))
                    var payload = input.diagnosticPayload
                    payload["reader"] = reader
                    Task { await RetAInClient.shared.diagnostic(kind: "unusable-share", payload: payload) }
                }
            }
            show(root)
        }
    }

    private func show(_ root: AnyView) {
        for old in children { old.willMove(toParent: nil); old.view.removeFromSuperview(); old.removeFromParent() }
        let host = UIHostingController(rootView: root)
        addChild(host)
        host.view.frame = view.bounds
        host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(host.view)
        host.didMove(toParent: self)
    }
}

struct MessageView: View {
    let title: String; let detail: String; let onDone: () -> Void
    var body: some View {
        NavigationStack {
            VStack(spacing: 12) { Text(title).font(.headline); Text(detail).font(.callout).foregroundStyle(.secondary).multilineTextAlignment(.center) }
                .padding().navigationTitle("RetAIn").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Done") { onDone() } } }
        }
    }
}

struct CaptureView: View {
    let word: String; let onDone: () -> Void
    @State private var result: Word?
    @State private var error: String?
    var body: some View {
        NavigationStack {
            Group {
                if let w = result { WordCardView(word: w) }
                else if let e = error { Text(e).foregroundStyle(.secondary).padding() }
                else { ProgressView("Adding “\(word)”…") }
            }
            .navigationTitle("Captured").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Done") { onDone() } } }
        }
        .task {
            do { result = try await RetAInClient.shared.addWord(word) } catch { self.error = error.localizedDescription }
        }
    }
}
