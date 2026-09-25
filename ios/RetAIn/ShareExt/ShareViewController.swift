import SwiftUI
import UIKit

/// Principal class for both the share extension and the Safari action. No login here:
/// the session token comes from the app-group keychain. A single shared word → capture;
/// longer text → the transform sheet.
final class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        let source = (Bundle.main.bundleIdentifier ?? "").hasSuffix("action") ? "action-ext" : "share-ext"
        Task { @MainActor in
            let input = await ExtensionInput.gather(from: extensionContext, source: source)
            let done: () -> Void = { [weak self] in self?.extensionContext?.completeRequest(returningItems: nil) }
            let root: AnyView
            if !SessionStore.isSignedIn {
                root = AnyView(MessageView(title: "Open RetAIn once to sign in", detail: "Then sharing works from anywhere.", onDone: done))
            } else if let word = input.singleWord {
                root = AnyView(CaptureView(word: word, onDone: done))
            } else if let text = input.effectiveText {
                root = AnyView(SheetView(text: text, title: input.title, url: input.url, source: source, onDone: done))
            } else {
                root = AnyView(MessageView(title: "Nothing to read here",
                                           detail: "Select some text (at least a couple of sentences) and share the selection, or share a single word to capture it.",
                                           onDone: done))
            }
            let host = UIHostingController(rootView: root)
            addChild(host)
            host.view.frame = view.bounds
            host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            view.addSubview(host.view)
            host.didMove(toParent: self)
        }
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
