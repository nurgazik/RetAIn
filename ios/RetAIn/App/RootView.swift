import SwiftUI
import WidgetKit

struct RootView: View {
    @Environment(SessionState.self) private var session
    @Environment(\.scenePhase) private var scenePhase
    var body: some View {
        if session.signedIn {
            TabView {
                TransformView().tabItem { Label("RetAInize", systemImage: "sparkles") }
                WordsView().tabItem { Label("Words", systemImage: "character.book.closed") }
                ReadsView().tabItem { Label("My Reads", systemImage: "books.vertical") }
                SettingsView().tabItem { Label("Settings", systemImage: "gearshape") }
            }
            // Keep the widget's word copy fresh even if the Words tab is never opened.
            .onChange(of: scenePhase, initial: true) { _, phase in if phase == .active { Task { await cacheWords() } } }
        } else {
            SignInView()
        }
    }

    private func cacheWords() async {
        guard let words = try? await RetAInClient.shared.words() else { return }
        WordsStore.replaceAll(words); WidgetCenter.shared.reloadAllTimelines()
    }
}
